document.addEventListener('DOMContentLoaded', () => {
    // State Variables
    let currentGridSize = 3;
    let charactersMap = {};
    let revealedClues = [];
    let selectedCharId = null;
    let hintData = null;

    // DOM Elements
    const puzzleSelect = document.getElementById('puzzle-select');
    const btnLoad = document.getElementById('btn-load');
    const btnRestart = document.getElementById('btn-restart');
    const btnHint = document.getElementById('btn-hint');
    const btnAutoStep = document.getElementById('btn-auto-step');
    const btnAutoSolve = document.getElementById('btn-auto-solve');

    const gridContainer = document.getElementById('grid-container');
    const puzzleInfoBadge = document.getElementById('puzzle-info-badge');
    const uniquenessTag = document.getElementById('uniqueness-tag');
    const alertBanner = document.getElementById('alert-banner');
    
    const cluesList = document.getElementById('clues-list');
    const clueCountBadge = document.getElementById('clue-count-badge');
    const traceList = document.getElementById('trace-list');
    const stepCountBadge = document.getElementById('step-count-badge');

    const verdictModal = document.getElementById('verdict-modal');
    const modalCharTitle = document.getElementById('modal-char-title');
    const modalCharInfo = document.getElementById('modal-char-info');
    const modalClose = document.getElementById('modal-close');
    const btnVerdictInnocent = document.getElementById('btn-verdict-innocent');
    const btnVerdictCriminal = document.getElementById('btn-verdict-criminal');

    const hintModal = document.getElementById('hint-modal');
    const hintClose = document.getElementById('hint-close');
    const hintContent = document.getElementById('hint-content');
    const hintApplyBtn = document.getElementById('hint-apply-btn');

    // Initialize App
    init();

    async function init() {
        await fetchPuzzlesList();
        const initialFile = puzzleSelect.value || 'puzzle_01_3x3_easy.json';
        await loadPuzzle(initialFile);
        setupEventListeners();
    }

    function setupEventListeners() {
        btnLoad.addEventListener('click', () => {
            const filename = puzzleSelect.value;
            if (filename) {
                loadPuzzle(filename);
            }
        });

        btnRestart.addEventListener('click', restartPuzzle);
        btnHint.addEventListener('click', fetchHint);
        btnAutoStep.addEventListener('click', runAutoStep);
        btnAutoSolve.addEventListener('click', runAutoSolve);

        modalClose.addEventListener('click', () => verdictModal.classList.add('hidden'));
        hintClose.addEventListener('click', () => hintModal.classList.add('hidden'));

        btnVerdictInnocent.addEventListener('click', () => submitVerdict('INNOCENT'));
        btnVerdictCriminal.addEventListener('click', () => submitVerdict('CRIMINAL'));

        hintApplyBtn.addEventListener('click', async () => {
            if (hintData && hintData.character_id) {
                hintModal.classList.add('hidden');
                selectedCharId = hintData.character_id;
                await submitVerdict(hintData.suggested_status);
            }
        });
    }

    async function fetchPuzzlesList() {
        try {
            const res = await fetch('/api/puzzles');
            const data = await res.json();
            puzzleSelect.innerHTML = '';
            data.puzzles.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.filename;
                opt.textContent = p.title || p.filename;
                puzzleSelect.appendChild(opt);
            });
        } catch (err) {
            console.error('Failed to fetch puzzle list:', err);
        }
    }

    async function loadPuzzle(filename) {
        try {
            showAlert('Loading puzzle...', 'warning');
            const res = await fetch('/api/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename })
            });
            const data = await res.json();

            currentGridSize = data.grid_size;
            charactersMap = {};
            data.characters.forEach(c => charactersMap[c.id] = c);
            revealedClues = data.revealed_clues;

            puzzleInfoBadge.textContent = `${data.title || filename} (${currentGridSize}x${currentGridSize})`;
            if (data.is_unique) {
                uniquenessTag.textContent = `Unique Solution Guaranteed (1 Solution)`;
                uniquenessTag.style.color = 'var(--accent-emerald)';
            } else {
                uniquenessTag.textContent = `Multiple/No Solutions (${data.uniqueness_count})`;
                uniquenessTag.style.color = 'var(--accent-crimson)';
            }

            renderBoard();
            renderClues();
            traceList.innerHTML = '<div class="empty-state">Run Auto Step or Auto Solve to view AI reasoning steps.</div>';
            stepCountBadge.textContent = '0 Steps';

            showAlert(`Loaded ${data.title || filename} successfully.`, 'success');
        } catch (err) {
            console.error(err);
            showAlert('Error loading puzzle.', 'error');
        }
    }

    async function restartPuzzle() {
        try {
            const res = await fetch('/api/restart', { method: 'POST' });
            const data = await res.json();
            charactersMap = {};
            data.characters.forEach(c => charactersMap[c.id] = c);
            revealedClues = data.revealed_clues;

            renderBoard();
            renderClues();
            traceList.innerHTML = '<div class="empty-state">Run Auto Step or Auto Solve to view AI reasoning steps.</div>';
            stepCountBadge.textContent = '0 Steps';

            showAlert('Puzzle restarted.', 'warning');
        } catch (err) {
            console.error(err);
        }
    }

    function renderBoard() {
        gridContainer.style.gridTemplateColumns = `repeat(${currentGridSize}, 1fr)`;
        gridContainer.innerHTML = '';

        for (let r = 1; r <= currentGridSize; r++) {
            for (let c = 1; c <= currentGridSize; c++) {
                const charId = `${String.fromCharCode(64 + c)}${r}`;
                const char = charactersMap[charId];

                const card = document.createElement('div');
                card.className = 'char-card';
                card.dataset.id = charId;

                const status = char ? char.revealed_status : 'UNKNOWN';
                if (status === 'INNOCENT') card.classList.add('revealed-innocent');
                if (status === 'CRIMINAL') card.classList.add('revealed-criminal');

                card.innerHTML = `
                    <div class="card-header">
                        <span class="coord-label">${char ? char.coord : charId}</span>
                        <span class="status-badge ${status.toLowerCase()}">${status}</span>
                    </div>
                    <div>
                        <div class="char-name">${char ? char.name : charId}</div>
                        <div class="char-job">${char ? char.job : ''}</div>
                    </div>
                    <div class="card-footer">
                        <span class="clue-indicator">${char && char.clue_ids.length > 0 ? '📜 Clue Holder' : ''}</span>
                    </div>
                `;

                card.addEventListener('click', () => openVerdictModal(charId));
                gridContainer.appendChild(card);
            }
        }
    }

    function renderClues() {
        cluesList.innerHTML = '';
        clueCountBadge.textContent = `${revealedClues.length} Clues`;

        if (revealedClues.length === 0) {
            cluesList.innerHTML = '<div class="empty-state">No revealed clues yet.</div>';
            return;
        }

        revealedClues.forEach(clue => {
            const item = document.createElement('div');
            item.className = 'clue-item';
            
            const owner = charactersMap[clue.owner_id];
            const ownerName = owner ? owner.name : clue.owner_id;

            item.innerHTML = `
                <div class="clue-item-header">
                    <span class="clue-owner">Owner: ${ownerName} (${clue.owner_id})</span>
                    <span class="clue-type-tag">${clue.type}</span>
                </div>
                <div class="clue-desc">${clue.description}</div>
            `;

            // Highlight referenced region cells on hover / click
            item.addEventListener('mouseenter', () => highlightClueRegion(clue));
            item.addEventListener('mouseleave', clearRegionHighlights);

            cluesList.appendChild(item);
        });
    }

    function highlightClueRegion(clue) {
        clearRegionHighlights();

        let targetIds = [];
        const params = clue.params;

        if (clue.type === 'FACT') {
            targetIds = [params.person];
        } else if (clue.type === 'SAME' || clue.type === 'DIFFERENT') {
            targetIds = [params.person1, params.person2];
        } else if (['EXACTLY', 'AT_LEAST', 'AT_MOST', 'PARITY'].includes(clue.type)) {
            const region = params.region;
            if (region.type === 'ROW') {
                const r = region.param;
                for (let c = 1; c <= currentGridSize; c++) {
                    targetIds.push(`${String.fromCharCode(64 + c)}${r}`);
                }
            } else if (region.type === 'COLUMN') {
                const colLetter = String(region.param).toUpperCase();
                for (let r = 1; r <= currentGridSize; r++) {
                    targetIds.push(`${colLetter}${r}`);
                }
            } else if (region.type === 'EXPLICIT') {
                targetIds = region.param;
            }
        } else if (clue.type === 'BETWEEN') {
            targetIds = [params.char1, params.char2];
        }

        targetIds.forEach(id => {
            const card = document.querySelector(`.char-card[data-id="${id}"]`);
            if (card) card.classList.add('highlight-region');
        });
    }

    function clearRegionHighlights() {
        document.querySelectorAll('.char-card').forEach(card => card.classList.remove('highlight-region'));
    }

    function openVerdictModal(charId) {
        selectedCharId = charId;
        const char = charactersMap[charId];
        if (!char) return;

        if (char.revealed_status !== 'UNKNOWN') {
            showAlert(`${char.name} is already revealed as ${char.revealed_status}.`, 'warning');
            return;
        }

        modalCharTitle.textContent = `Verdict for ${char.name} (${char.coord})`;
        modalCharInfo.textContent = `Job: ${char.job} | Current Status: UNKNOWN`;
        verdictModal.classList.remove('hidden');
    }

    async function submitVerdict(claimedStatus) {
        if (!selectedCharId) return;

        verdictModal.classList.add('hidden');
        try {
            const res = await fetch('/api/verdict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ character_id: selectedCharId, status: claimedStatus })
            });

            const data = await res.json();
            if (data.error) {
                showAlert(`Error: ${data.error}`, 'error');
                return;
            }

            if (data.verdict_status === 'ACCEPTED') {
                showAlert(data.message, 'success');
            } else if (data.verdict_status === 'CONTRADICTED') {
                showAlert(data.message, 'error');
            } else {
                showAlert(data.message, 'warning');
            }

            // Update local state
            charactersMap = {};
            data.characters.forEach(c => charactersMap[c.id] = c);
            revealedClues = data.revealed_clues;

            renderBoard();
            renderClues();
        } catch (err) {
            console.error(err);
            showAlert('Network error submitting verdict.', 'error');
        }
    }

    async function fetchHint() {
        try {
            const res = await fetch('/api/hint');
            const data = await res.json();

            if (!data.hint) {
                showAlert('No hint available: No character is forced by current public clues.', 'warning');
                return;
            }

            hintData = data.hint;
            
            const cluesHtml = hintData.relevant_clues.length > 0 
                ? `<ul style="margin: 5px 0 0 15px; padding-left: 0; text-align: left;">` + 
                  hintData.relevant_clues.map(c => `<li style="margin-bottom: 4px;">${c}</li>`).join('') + 
                  `</ul>`
                : `<p style="margin: 5px 0 0 0; color: var(--text-muted);">No specific clues target this character directly, use row/column counts.</p>`;

            hintContent.innerHTML = `
                <div style="margin-bottom: 12px;">
                    <strong>💡 Target Character:</strong> ${hintData.character_name} (${hintData.character_id}) at ${hintData.coord}
                </div>
                <div style="margin-bottom: 12px; background: rgba(255, 255, 255, 0.05); padding: 8px; border-radius: 4px;">
                    <strong>🔍 Relevant Clues to Consider:</strong><br>
                    ${cluesHtml}
                </div>
                <div id="hint-peek-container" style="margin-top: 10px;">
                    <button id="btn-peek-hint" class="btn btn-secondary" style="font-size: 11px; padding: 4px 8px; border: 1px solid rgba(255,255,255,0.2);">👁 Peek Answer</button>
                    <div id="hint-peek-content" class="hidden" style="margin-top: 10px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 8px;">
                        <strong>Suggested Verdict:</strong> <span style="color: var(--accent-emerald); font-weight: bold;">${hintData.suggested_status}</span><br>
                        <strong>Explanation:</strong> ${hintData.explanation}<br>
                        <em style="font-size: 11px; color: var(--text-muted); display: block; margin-top: 4px;">${hintData.dpll_stats}</em>
                    </div>
                </div>
            `;

            hintModal.classList.remove('hidden');

            const btnPeek = document.getElementById('btn-peek-hint');
            const peekContent = document.getElementById('hint-peek-content');
            btnPeek.addEventListener('click', () => {
                peekContent.classList.toggle('hidden');
                btnPeek.innerText = peekContent.classList.contains('hidden') ? '👁 Peek Answer' : '🙈 Hide Answer';
            });
        } catch (err) {
            console.error(err);
        }
    }

    async function runAutoStep() {
        try {
            const res = await fetch('/api/auto-step', { method: 'POST' });
            const data = await res.json();

            if (!data.step_result) {
                showAlert('No character can be logically deduced at this point.', 'warning');
                return;
            }

            charactersMap = {};
            data.characters.forEach(c => charactersMap[c.id] = c);
            revealedClues = data.revealed_clues;

            renderBoard();
            renderClues();
            appendTraceItem(data.step_result);

            showAlert(`Auto Step: Proved ${data.step_result.character_name} as ${data.step_result.forced_status}.`, 'success');
        } catch (err) {
            console.error(err);
        }
    }

    async function runAutoSolve() {
        try {
            showAlert('AI Logic Agent running full DPLL deduction loop...', 'warning');
            
            // 1. Restart first to clear state
            const resetRes = await fetch('/api/restart', { method: 'POST' });
            const resetData = await resetRes.json();
            charactersMap = {};
            resetData.characters.forEach(c => charactersMap[c.id] = c);
            revealedClues = resetData.revealed_clues;
            renderBoard();
            renderClues();
            traceList.innerHTML = '';
            stepCountBadge.textContent = '0 Steps';

            // 2. Fetch full trace from solve
            const res = await fetch('/api/auto-solve', { method: 'POST' });
            const data = await res.json();

            if (!data.trace || data.trace.length === 0) {
                showAlert('No steps needed or could be solved.', 'warning');
                return;
            }

            // 3. Play animation steps sequentially
            for (let i = 0; i < data.trace.length; i++) {
                const step = data.trace[i];

                // Update character status
                if (charactersMap[step.character_id]) {
                    charactersMap[step.character_id].revealed_status = step.forced_status;
                }

                // Add newly revealed clues
                if (step.newly_revealed_clues) {
                    step.newly_revealed_clues.forEach(newClue => {
                        if (!revealedClues.some(c => c.id === newClue.id)) {
                            revealedClues.push(newClue);
                        }
                    });
                }

                // Render board and clues
                renderBoard();
                renderClues();

                // Append trace item and update step count
                appendTraceItem(step);
                stepCountBadge.textContent = `${i + 1} Steps`;

                // Highlight the cell that was updated
                const cellElement = document.querySelector(`.char-card[data-id="${step.character_id}"]`);
                if (cellElement) {
                    cellElement.classList.add('pulse-highlight');
                }

                // Wait 800ms between steps
                await new Promise(resolve => setTimeout(resolve, 800));
            }

            showAlert(`Puzzle fully solved by AI Agent in ${data.total_steps} steps!`, 'success');
        } catch (err) {
            console.error(err);
            showAlert('Error running auto solve.', 'error');
        }
    }

    function appendTraceItem(stepRes) {
        if (traceList.querySelector('.empty-state')) {
            traceList.innerHTML = '';
        }

        const item = document.createElement('div');
        item.className = 'trace-item';
        item.innerHTML = `
            <div class="trace-header">
                <span class="trace-step">Step ${stepRes.step || '#'}: ${stepRes.character_name} (${stepRes.coord})</span>
                <span style="color: var(--primary-cyan);">${stepRes.forced_status}</span>
            </div>
            <div>${stepRes.message}</div>
            <div class="trace-stats">${stepRes.solver_stats}</div>
        `;
        traceList.prepend(item);
    }

    function showAlert(msg, type) {
        alertBanner.textContent = msg;
        alertBanner.className = `alert-banner ${type}`;
        setTimeout(() => {
            alertBanner.classList.add('hidden');
        }, 5000);
    }
});
