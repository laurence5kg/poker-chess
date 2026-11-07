// Main Application UI Controller with Bilingual i18n & Theme Management

document.addEventListener('DOMContentLoaded', () => {
    // Initialize i18n and Themes
    window.I18N.init();

    const game = new GameEngine();
    window.gameInstance = game;

    let activeClash = null;
    let autoCloseTimer = null;

    // UI Elements
    const boardEl = document.getElementById('boardGrid');
    const UI_ICONS = {
        settings: `<svg class="ui-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`,
        newGame: `<svg class="ui-icon" viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"></polyline><polyline points="23 20 23 14 17 14"></polyline><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path></svg>`,
        home: `<svg class="ui-icon" viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>`,
        rulebook: `<svg class="ui-icon" viewBox="0 0 24 24"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>`,
        dropSlot: `<svg class="ui-icon" style="margin:0 auto 4px; display:block; width:16px; height:16px;" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" stroke-dasharray="3 3"></rect><path d="M12 8v8M8 12h8"></path></svg>`,
        obstacle: `<svg class="ui-icon" style="width:16px; height:16px; margin:0; opacity:0.65;" viewBox="0 0 24 24"><path d="m8 3 4 8 5-5 5 15H2L8 3z"></path></svg>`
    };

    const statusBarEl = document.getElementById('statusBar');
    const turnDisplayEl = document.getElementById('turnDisplay');
    const uiDeployPhaseLabel = document.getElementById('uiDeployPhaseLabel');
    const redNativeEl = document.getElementById('redNative');
    const redMochigomaEl = document.getElementById('redMochigoma');
    const redCapEl = document.getElementById('redCap');
    const blackNativeEl = document.getElementById('blackNative');
    const blackMochigomaEl = document.getElementById('blackMochigoma');
    const blackCapEl = document.getElementById('blackCap');
    
    // Trays & Sidebar Sections
    const p1StartingTrayEl = document.getElementById('p1StartingTray');
    const p1MochigomaTrayEl = document.getElementById('p1MochigomaTray');
    const p2StartingTrayEl = document.getElementById('p2StartingTray');
    const p2MochigomaTrayEl = document.getElementById('p2MochigomaTray');
    const p1MochigomaSectionEl = document.getElementById('p1MochigomaSection');
    const p2MochigomaSectionEl = document.getElementById('p2MochigomaSection');
    const graveyardSectionEl = document.getElementById('graveyardSection');
    const graveyardListEl = document.getElementById('graveyardList');

    // Setup Toolbar Elements
    const setupToolbarEl = document.getElementById('setupToolbar');
    const setupCampCountEl = document.getElementById('setupCampCount');
    const setupReserveCountEl = document.getElementById('setupReserveCount');
    const setupUnplacedCountEl = document.getElementById('setupUnplacedCount');
    const setupStatusMessageEl = document.getElementById('setupStatusMessage');
    const setupAutoBtn = document.getElementById('setupAutoBtn');
    const setupClearBtn = document.getElementById('setupClearBtn');
    const setupConfirmBtn = document.getElementById('setupConfirmBtn');
    const setupUnplacedSectionEl = document.getElementById('setupUnplacedSection');
    const unplacedTrayEl = document.getElementById('unplacedTray');

    // Modals
    const clashModalEl = document.getElementById('clashModal');
    const clashAttackerEl = document.getElementById('clashAttacker');
    const clashDefenderEl = document.getElementById('clashDefender');
    const clashVerdictEl = document.getElementById('clashVerdict');
    const clashCloseBtn = document.getElementById('clashCloseBtn');

    const cardInspectModalEl = document.getElementById('cardInspectModal');
    const closeInspectBtn = document.getElementById('closeInspectBtn');
    const inspectTitleEl = document.getElementById('inspectTitle');
    const inspectCardContainerEl = document.getElementById('inspectCardContainer');
    const inspectCardInfoEl = document.getElementById('inspectCardInfo');

    if (closeInspectBtn) {
        closeInspectBtn.addEventListener('click', () => {
            if (cardInspectModalEl) cardInspectModalEl.style.display = 'none';
        });
    }
    if (cardInspectModalEl) {
        cardInspectModalEl.addEventListener('click', (e) => {
            if (e.target === cardInspectModalEl) cardInspectModalEl.style.display = 'none';
        });
    }

    const settingsModalEl = document.getElementById('settingsModal');
    const settingsBtn = document.getElementById('settingsBtn');
    const closeSettingsBtn = document.getElementById('closeSettingsBtn');
    const stgSoundToggleBtn = document.getElementById('stgSoundToggleBtn');
    const openRulebookFromStgBtn = document.getElementById('openRulebookFromStgBtn');

    const rulesModalEl = document.getElementById('rulesModal');
    const closeRulesBtn = document.getElementById('closeRulesBtn');
    const rulebookContentEl = document.getElementById('rulebookContent');

    const gameOverModalEl = document.getElementById('gameOverModal');
    const gameOverTitleEl = document.getElementById('gameOverTitle');
    const gameOverReasonEl = document.getElementById('gameOverReason');
    const gameOverNewGameBtn = document.getElementById('gameOverNewGameBtn');
    const gameOverHomeBtn = document.getElementById('gameOverHomeBtn');

    if (gameOverNewGameBtn) {
        gameOverNewGameBtn.addEventListener('click', () => {
            if (gameOverModalEl) gameOverModalEl.style.display = 'none';
            startNewGame();
        });
    }
    if (gameOverHomeBtn) {
        gameOverHomeBtn.addEventListener('click', () => {
            if (gameOverModalEl) gameOverModalEl.style.display = 'none';
            showHomepage();
        });
    }

    function showToast(message) {
        const toast = document.getElementById('toastNotice');
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add('visible');
        clearTimeout(toast.timer);
        toast.timer = setTimeout(() => {
            toast.classList.remove('visible');
        }, 2800);
    }

    function showGameOver(reason) {
        if (!gameOverModalEl) return;
        if (gameOverReasonEl) gameOverReasonEl.textContent = reason;
        if (gameOverTitleEl) {
            const isZh = window.I18N && window.I18N.currentLang === 'zh';
            gameOverTitleEl.textContent = isZh ? '对局结束' : 'GAME OVER';
        }
        gameOverModalEl.style.display = 'flex';
    }

    // Header & Screen Navigation
    const homepageScreenEl = document.getElementById('homepageScreen');
    const gameScreenEl = document.getElementById('gameScreen');
    const homeBtn = document.getElementById('homeBtn');
    const newGameBtn = document.getElementById('newGameBtn');
    const homeSettingsBtn = document.getElementById('homeSettingsBtn');
    const homeRulebookBtn = document.getElementById('homeRulebookBtn');

    function showHomepage() {
        if (homepageScreenEl) homepageScreenEl.style.display = 'flex';
        if (gameScreenEl) gameScreenEl.style.display = 'none';
    }

    function showGame() {
        if (homepageScreenEl) homepageScreenEl.style.display = 'none';
        if (gameScreenEl) gameScreenEl.style.display = 'flex';
    }

    if (homeBtn) {
        homeBtn.addEventListener('click', showHomepage);
    }

    const tabBtnPve = document.getElementById('tabBtnPve');
    const tabBtnPvp = document.getElementById('tabBtnPvp');
    const panelPveEl = document.getElementById('panelPve');
    const panelPvpEl = document.getElementById('panelPvp');

    const launchPveBtn = document.getElementById('launchPveBtn');
    const launchPvpBtn = document.getElementById('launchPvpBtn');

    const pvp1v1SubOptionsEl = document.getElementById('pvp1v1SubOptions');
    const pvp2v2SubOptionsEl = document.getElementById('pvp2v2SubOptions');
    const pvpFfaSubOptionsEl = document.getElementById('pvpFfaSubOptions');
    const homeSeatingSelectEl = document.getElementById('homeSeatingSelect');

    // Tabs toggle
    if (tabBtnPve && tabBtnPvp) {
        tabBtnPve.addEventListener('click', () => {
            tabBtnPve.classList.add('active');
            tabBtnPvp.classList.remove('active');
            panelPveEl.classList.add('active');
            panelPvpEl.classList.remove('active');
        });

        tabBtnPvp.addEventListener('click', () => {
            tabBtnPvp.classList.add('active');
            tabBtnPve.classList.remove('active');
            panelPvpEl.classList.add('active');
            panelPveEl.classList.remove('active');
        });
    }

    // PvP sub-mode switch
    document.querySelectorAll('input[name="pvpModeType"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const val = e.target.value;
            document.querySelectorAll('input[name="pvpModeType"]').forEach(r => {
                const parent = r.closest('.option-card');
                if (parent) parent.classList.toggle('selected', r.checked);
            });

            if (pvp1v1SubOptionsEl) pvp1v1SubOptionsEl.style.display = (val === '1v1') ? 'block' : 'none';
            if (pvp2v2SubOptionsEl) pvp2v2SubOptionsEl.style.display = (val === '2v2') ? 'block' : 'none';
            if (pvpFfaSubOptionsEl) pvpFfaSubOptionsEl.style.display = (val === 'ffa') ? 'block' : 'none';
        });
    });

    // Option cards selection styling updates
    ['pveAiLevel', 'pveSide', 'pvp1v1Side', 'pvp2v2Alliance', 'pvpFfaSeat'].forEach(groupName => {
        document.querySelectorAll(`input[name="${groupName}"]`).forEach(radio => {
            radio.addEventListener('change', () => {
                document.querySelectorAll(`input[name="${groupName}"]`).forEach(r => {
                    const parentCard = r.closest('.option-card') || r.closest('.side-choice-card');
                    if (parentCard) parentCard.classList.toggle('selected', r.checked);
                });
            });
        });
    });

    // Launch PvE
    if (launchPveBtn) {
        launchPveBtn.addEventListener('click', () => {
            const aiRadio = document.querySelector('input[name="pveAiLevel"]:checked');
            const sideRadio = document.querySelector('input[name="pveSide"]:checked');
            const aiLevel = aiRadio ? aiRadio.value : 'medium';
            const humanSide = sideRadio ? sideRadio.value : 'red';

            showGame();
            startNewGameWithOptions({
                mode: 'pve',
                aiLevel,
                humanSide
            });
            if (window.I18N && typeof showToast === 'function') {
                showToast(window.I18N.t('turn_1_hint'));
            }
        });
    }

    // Launch PvP
    if (launchPvpBtn) {
        launchPvpBtn.addEventListener('click', () => {
            const pvpTypeRadio = document.querySelector('input[name="pvpModeType"]:checked');
            const pvpType = pvpTypeRadio ? pvpTypeRadio.value : '1v1';

            showGame();
            if (pvpType === '1v1') {
                const sideRadio = document.querySelector('input[name="pvp1v1Side"]:checked');
                const humanSide = sideRadio ? sideRadio.value : 'red';
                startNewGameWithOptions({
                    mode: 'pvp',
                    humanSide
                });
                if (window.I18N && typeof showToast === 'function') {
                    showToast(window.I18N.t('turn_1_hint'));
                }
            } else if (pvpType === '2v2') {
                const allianceRadio = document.querySelector('input[name="pvp2v2Alliance"]:checked');
                const pvpAlliance = allianceRadio ? allianceRadio.value : 'clubs';
                const seating = homeSeatingSelectEl ? homeSeatingSelectEl.value : 'opposite';
                startNewGameWithOptions({
                    mode: '4p_2v2',
                    playerCount: 4,
                    fourPlayerMode: '2v2',
                    pvpAlliance,
                    seating
                });
            } else if (pvpType === 'ffa') {
                const seatRadio = document.querySelector('input[name="pvpFfaSeat"]:checked');
                const playerSeat = seatRadio ? seatRadio.value : 'a';
                startNewGameWithOptions({
                    mode: '4p_ffa',
                    playerCount: 4,
                    fourPlayerMode: 'ffa',
                    playerSeat
                });
            }
        });
    }

    // Clash Modal Space / Enter listener
    window.addEventListener('keydown', (e) => {
        if (e.code === 'Space' || e.code === 'Enter') {
            if (clashModalEl.style.display === 'flex') {
                closeClashModal();
            }
        }
    });

    if (newGameBtn) {
        newGameBtn.addEventListener('click', () => {
            startNewGame();
        });
    }

    function openSettingsModal() {
        const langRadios = document.getElementsByName('langRadio');
        langRadios.forEach(r => r.checked = (r.value === window.I18N.currentLang));

        const themeRadios = document.getElementsByName('themeRadio');
        themeRadios.forEach(r => r.checked = (r.value === window.I18N.currentTheme));

        const cardStyleRadios = document.getElementsByName('cardStyleRadio');
        cardStyleRadios.forEach(r => r.checked = (r.value === window.I18N.currentCardStyle));

        updateSoundBtnState();
        settingsModalEl.style.display = 'flex';
    }

    if (settingsBtn) {
        settingsBtn.addEventListener('click', openSettingsModal);
    }
    if (homeSettingsBtn) {
        homeSettingsBtn.addEventListener('click', openSettingsModal);
    }
    if (homeRulebookBtn) {
        homeRulebookBtn.addEventListener('click', () => {
            renderRulebookContent();
            rulesModalEl.style.display = 'flex';
        });
    }

    closeSettingsBtn.addEventListener('click', () => {
        settingsModalEl.style.display = 'none';
    });

    // Radio button listeners
    document.querySelectorAll('input[name="langRadio"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            window.I18N.setLang(e.target.value);
            updateAllLocalizedText();
            render();
        });
    });

    document.querySelectorAll('input[name="themeRadio"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            window.I18N.setTheme(e.target.value);
        });
    });

    document.querySelectorAll('input[name="cardStyleRadio"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            window.I18N.setCardStyle(e.target.value);
            render();
        });
    });

    function updateSoundBtnState() {
        stgSoundToggleBtn.textContent = window.soundFX.enabled ? 
            window.I18N.t('sound_enabled') : 
            window.I18N.t('sound_muted');
    }

    stgSoundToggleBtn.addEventListener('click', () => {
        window.soundFX.enabled = !window.soundFX.enabled;
        updateSoundBtnState();
    });

    openRulebookFromStgBtn.addEventListener('click', () => {
        settingsModalEl.style.display = 'none';
        renderRulebookContent();
        rulesModalEl.style.display = 'flex';
    });

    closeRulesBtn.addEventListener('click', () => {
        rulesModalEl.style.display = 'none';
    });

    // Close Clash Modal reliably
    function closeClashModal() {
        if (autoCloseTimer) {
            clearTimeout(autoCloseTimer);
            autoCloseTimer = null;
        }
        clashModalEl.style.display = 'none';
        game.lastClashResult = null;
        activeClash = null;
        render();

        if (game.gameState === 'gameover') {
            setTimeout(() => {
                showGameOver(game.winReason);
            }, 100);
            return;
        }

        if (game.mode === 'pve' && game.currentTurn === game.botSide && game.gameState === 'playing') {
            setTimeout(() => {
                game.runBotTurn();
                render();
            }, 500);
        }
    }

    clashCloseBtn.addEventListener('click', closeClashModal);
    clashModalEl.addEventListener('click', (e) => {
        if (e.target === clashModalEl) closeClashModal();
    });

    // Setup Toolbar Handlers
    setupAutoBtn.addEventListener('click', () => {
        if (game.playerCount === 4) {
            game.autoSetupAll4P();
        } else {
            game.autoSetup(game.setupPlayer);
        }
        window.soundFX.playCardFlip();
        render();
    });

    setupClearBtn.addEventListener('click', () => {
        if (game.playerCount === 4) {
            game.autoSetupAll4P();
        } else {
            game.initSetup(game.setupPlayer);
        }
        window.soundFX.playCardFlip();
        render();
    });

    function handlePutCardIntoReserve(player, slotIdx = null) {
        const reserves = game.hands[player].startingReserves;

        // 1. From unplaced tray
        if (game.selectedUnplacedIndex !== null) {
            const card = game.unplacedCards[player].splice(game.selectedUnplacedIndex, 1)[0];
            game.selectedUnplacedIndex = null;

            if (slotIdx !== null && slotIdx < reserves.length) {
                // Swap with existing card in that slot
                const oldCard = reserves[slotIdx];
                reserves[slotIdx] = card;
                game.unplacedCards[player].push(oldCard);
            } else if (reserves.length < 2) {
                reserves.push(card);
            } else {
                // Already 2 cards: replace the first one
                const oldCard = reserves.splice(0, 1)[0];
                reserves.push(card);
                game.unplacedCards[player].push(oldCard);
            }

            window.soundFX.playCardFlip();
            render();
            return;
        }

        // 2. From board
        if (game.selectedTile) {
            const card = game.board[game.selectedTile.r][game.selectedTile.c];
            if (card && card.player === player) {
                const r = game.selectedTile.r;
                const c = game.selectedTile.c;
                game.board[r][c] = null;
                game.selectedTile = null;

                if (slotIdx !== null && slotIdx < reserves.length) {
                    const oldCard = reserves[slotIdx];
                    reserves[slotIdx] = card;
                    game.board[r][c] = oldCard;
                } else if (reserves.length < 2) {
                    reserves.push(card);
                } else {
                    const oldCard = reserves.splice(0, 1)[0];
                    reserves.push(card);
                    game.board[r][c] = oldCard;
                }

                window.soundFX.playCardFlip();
                render();
                return;
            }
        }
    }

    setupConfirmBtn.addEventListener('click', () => {
        if (window.networkClient && window.networkClient.isOnlineMatch) {
            const myColor = window.networkClient.playerColor || game.setupPlayer;
            const val = game.validateSetup(myColor);
            if (!val.valid) {
                if (window.soundFX && typeof window.soundFX.playIllegalMove === 'function') {
                    window.soundFX.playIllegalMove();
                }
                setupConfirmBtn.classList.remove('btn-shake');
                void setupConfirmBtn.offsetWidth;
                setupConfirmBtn.classList.add('btn-shake');
                showToast(val.errors.join('\n'));
                render();
                return;
            }
            const minRow = myColor === 'red' ? 0 : 7;
            const maxRow = myColor === 'red' ? 4 : 11;
            const camp = [];
            for (let r = minRow; r <= maxRow; r++) {
                for (let c = 0; c < 5; c++) {
                    const card = game.board[r][c];
                    camp.push({ r, c, rank: card.rank, suit: card.suit });
                }
            }
            const reserves = game.hands[myColor].startingReserves.map(c => ({
                rank: c.rank,
                suit: c.suit
            }));
            window.networkClient.submitLayout(camp, reserves);
            setupConfirmBtn.disabled = true;
            setupConfirmBtn.textContent = window.I18N ? window.I18N.t('waiting_for_opponent') : 'Waiting...';
            showToast(window.I18N ? window.I18N.t('waiting_for_opponent') : 'Waiting for opponent...');

            clearTimeout(window.__setupConfirmWatchdog);
            window.__setupConfirmWatchdog = setTimeout(() => {
                if (game.gameState === 'setup' && setupConfirmBtn && setupConfirmBtn.disabled) {
                    setupConfirmBtn.disabled = false;
                    setupConfirmBtn.textContent = 'Retry Confirm';
                    showToast('Server did not respond in time. Please tap Retry.');
                }
            }, 12000);
            return;
        }

        if (game.playerCount === 4) {
            game.gameState = 'playing';
            window.soundFX.playClash();
            render();
            return;
        }
        const res = game.confirmSetup(game.setupPlayer);
        if (!res.valid) {
            showToast(res.errors.join('\n'));
        } else {
            window.soundFX.playClash();
            render();
        }
    });

    function startNewGameWithOptions(options = {}) {
        if (autoCloseTimer) clearTimeout(autoCloseTimer);
        game.lastClashResult = null;
        activeClash = null;
        clashModalEl.style.display = 'none';
        if (gameOverModalEl) gameOverModalEl.style.display = 'none';

        game.resetForNewGame(options);
        render();
    }

    function startNewGame() {
        startNewGameWithOptions({
            mode: game.mode,
            playerCount: game.playerCount,
            fourPlayerMode: game.fourPlayerMode,
            humanSide: game.humanSide,
            aiLevel: game.aiLevel,
            seating: game.customSeatingChoice || 'opposite',
            pvpAlliance: game.pvpAlliance || 'clubs',
            playerSeat: game.playerSeat || 'a'
        });
    }

    // Dynamic Localization of DOM Elements
    function updateAllLocalizedText() {
        const t = (k, p) => window.I18N.t(k, p);

        // Header (3 buttons only on game screen, plus home controls)
        if (document.getElementById('uiTitle')) document.getElementById('uiTitle').textContent = t('title');
        if (document.getElementById('uiSubtitle')) document.getElementById('uiSubtitle').textContent = t('subtitle');
        if (newGameBtn) newGameBtn.textContent = t('new_game');
        if (settingsBtn) settingsBtn.textContent = t('settings');
        if (homeSettingsBtn) homeSettingsBtn.textContent = t('settings');
        if (homeRulebookBtn) homeRulebookBtn.textContent = t('rulebook_btn');
        if (homeBtn) homeBtn.textContent = t('home');

        // Homepage texts
        if (document.getElementById('homeTitle')) document.getElementById('homeTitle').textContent = t('homepage_title');
        if (document.getElementById('homeSubtitle')) document.getElementById('homeSubtitle').textContent = t('homepage_subtitle');
        if (document.getElementById('tabBtnPve')) document.getElementById('tabBtnPve').textContent = t('tab_pve');
        if (document.getElementById('tabBtnPvp')) document.getElementById('tabBtnPvp').textContent = t('tab_pvp');
        if (document.getElementById('homeAiTitle')) document.getElementById('homeAiTitle').textContent = t('ai_difficulty_title');
        if (document.getElementById('homeAiLowTitle')) document.getElementById('homeAiLowTitle').textContent = t('ai_level_low');
        if (document.getElementById('homeAiMedTitle')) document.getElementById('homeAiMedTitle').textContent = t('ai_level_medium');
        if (document.getElementById('homeAiHighTitle')) document.getElementById('homeAiHighTitle').textContent = t('ai_level_high');
        if (document.getElementById('homeSideTitle')) document.getElementById('homeSideTitle').textContent = t('side_select_title');
        if (document.getElementById('homePveSideRed')) document.getElementById('homePveSideRed').textContent = t('side_red');
        if (document.getElementById('homePveSideBlack')) document.getElementById('homePveSideBlack').textContent = t('side_black');
        if (document.getElementById('launchPveBtn')) document.getElementById('launchPveBtn').textContent = t('launch_pve_btn');

        if (document.getElementById('homePvpModeTitle')) document.getElementById('homePvpModeTitle').textContent = t('pvp_format_title');
        if (document.getElementById('homePvp1v1Title')) document.getElementById('homePvp1v1Title').textContent = t('pvp_1v1');
        if (document.getElementById('homePvp2v2Title')) document.getElementById('homePvp2v2Title').textContent = t('pvp_2v2');
        if (document.getElementById('homePvpFfaTitle')) document.getElementById('homePvpFfaTitle').textContent = t('pvp_ffa');
        if (document.getElementById('homePvp1v1SideTitle')) document.getElementById('homePvp1v1SideTitle').textContent = t('pvp_side_title_1v1');
        if (document.getElementById('homePvpSideRed')) document.getElementById('homePvpSideRed').textContent = t('side_red');
        if (document.getElementById('homePvpSideBlack')) document.getElementById('homePvpSideBlack').textContent = t('side_black');
        if (document.getElementById('homePvpAllianceTitle')) document.getElementById('homePvpAllianceTitle').textContent = t('pvp_alliance_title_2v2');
        if (document.getElementById('homeAllianceClubs')) document.getElementById('homeAllianceClubs').textContent = t('alliance_clubs');
        if (document.getElementById('homeAllianceHearts')) document.getElementById('homeAllianceHearts').textContent = t('alliance_hearts');
        if (document.getElementById('homePvpSeatingTitle')) document.getElementById('homePvpSeatingTitle').textContent = t('pvp_seating_title_2v2');
        if (document.getElementById('homeOptSeatOpposite')) document.getElementById('homeOptSeatOpposite').textContent = t('seating_opposite');
        if (document.getElementById('homeOptSeatAdjNwSe')) document.getElementById('homeOptSeatAdjNwSe').textContent = t('seating_adj_nw_se');
        if (document.getElementById('homeOptSeatAdjNeSw')) document.getElementById('homeOptSeatAdjNeSw').textContent = t('seating_adj_ne_sw');
        if (document.getElementById('homePvpFfaSeatTitle')) document.getElementById('homePvpFfaSeatTitle').textContent = t('seat_select_title_ffa');
        if (document.getElementById('homeSeatA')) document.getElementById('homeSeatA').textContent = t('seat_a');
        if (document.getElementById('homeSeatB')) document.getElementById('homeSeatB').textContent = t('seat_b');
        if (document.getElementById('homeSeatC')) document.getElementById('homeSeatC').textContent = t('seat_c');
        if (document.getElementById('homeSeatD')) document.getElementById('homeSeatD').textContent = t('seat_d');
        if (document.getElementById('launchPvpBtn')) document.getElementById('launchPvpBtn').textContent = t('launch_pvp_btn');

        // Status bar
        if (document.getElementById('uiRedArmyLabel')) document.getElementById('uiRedArmyLabel').textContent = t('red_army');
        if (document.getElementById('uiRedNativeLabel')) document.getElementById('uiRedNativeLabel').textContent = t('native');
        if (document.getElementById('uiRedMochiLabel')) document.getElementById('uiRedMochiLabel').textContent = t('mochigoma');
        if (document.getElementById('uiRedCapLabel')) document.getElementById('uiRedCapLabel').textContent = t('cap');
        if (document.getElementById('uiBlackArmyLabel')) document.getElementById('uiBlackArmyLabel').textContent = t('black_army');
        if (document.getElementById('uiBlackNativeLabel')) document.getElementById('uiBlackNativeLabel').textContent = t('native');
        if (document.getElementById('uiBlackMochiLabel')) document.getElementById('uiBlackMochiLabel').textContent = t('mochigoma');
        if (document.getElementById('uiBlackCapLabel')) document.getElementById('uiBlackCapLabel').textContent = t('cap');

        // Deployment toolbar
        document.getElementById('uiDeployPhaseLabel').textContent = t('deployment_phase');
        document.getElementById('uiCampLabel').textContent = t('camp');
        document.getElementById('uiReservesLabel').textContent = t('reserves');
        document.getElementById('uiUnplacedLabel').textContent = t('unplaced');
        setupAutoBtn.textContent = game.playerCount === 4 ? t('auto_fill_all') : t('auto_fill');
        setupClearBtn.textContent = t('clear_formation');
        setupConfirmBtn.textContent = game.playerCount === 4 ? t('start_battle_4p') : t('confirm_battle');

        // Sidebars
        if (document.getElementById('uiP2StartingHeader')) document.getElementById('uiP2StartingHeader').textContent = t('p2_starting_reserve');
        if (document.getElementById('uiP2MochiHeader')) document.getElementById('uiP2MochiHeader').textContent = t('p2_mochigoma');
        if (document.getElementById('uiGraveyardHeader')) document.getElementById('uiGraveyardHeader').textContent = t('graveyard');

        if (document.getElementById('uiUnplacedHeader')) document.getElementById('uiUnplacedHeader').textContent = t('unplaced_cards');
        if (document.getElementById('uiP1StartingHeader')) document.getElementById('uiP1StartingHeader').textContent = t('p1_starting_reserve');
        if (document.getElementById('uiP1MochiHeader')) document.getElementById('uiP1MochiHeader').textContent = t('p1_mochigoma');

        // Tray empty placeholders
        p1StartingTrayEl.setAttribute('data-empty-text', t('empty_reserve'));
        p1MochigomaTrayEl.setAttribute('data-empty-text', t('empty_reserve'));
        p2StartingTrayEl.setAttribute('data-empty-text', t('empty_reserve'));
        p2MochigomaTrayEl.setAttribute('data-empty-text', t('empty_reserve'));

        // Settings modal
        document.getElementById('stgModalTitle').textContent = t('settings_title');
        document.getElementById('stgLangHeading').textContent = t('language_heading');
        document.getElementById('stgCardStyleHeading').textContent = t('card_style_heading');
        document.getElementById('stgStyleSimplified').textContent = t('style_simplified');
        document.getElementById('stgStyleArt').textContent = t('style_art');
        document.getElementById('stgThemeHeading').textContent = t('theme_heading');
        document.getElementById('stgThemeFelt').textContent = t('theme_felt');
        document.getElementById('stgThemeWood').textContent = t('theme_wood');
        document.getElementById('stgThemeObsidian').textContent = t('theme_obsidian');
        document.getElementById('stgSoundHeading').textContent = t('sound_heading');
        document.getElementById('stgSoundDesc').textContent = t('sound_desc');
        updateSoundBtnState();
        document.getElementById('stgRulebookHeading').textContent = t('rulebook_heading');
        openRulebookFromStgBtn.textContent = t('rulebook_open');
        closeSettingsBtn.textContent = t('close_btn');

        // Clash modal
        document.getElementById('uiClashTitle').textContent = t('clash_title');
        clashCloseBtn.textContent = t('clash_continue');
    }

    function renderRulebookContent() {
        const isZh = window.I18N.currentLang === 'zh';
        if (isZh) {
            rulebookContentEl.innerHTML = `
                <h3 style="color:#d4af37; font-size:1.05rem; margin-bottom:8px;">棋子军衔与战斗层级</h3>
                <ul style="margin-left:20px; margin-bottom:14px; line-height:1.7;">
                    <li><strong>军旗 (司令部 / Joker)</strong>：不可移动、无防御力。敌方任何棋子进驻即算斩首成功，游戏立刻获胜！</li>
                    <li><strong>炸弹 (K 毁灭打击)</strong>：每次移动1格。与任何敌方单位相遇同归于尽 (双双进入墓地)。<em>特例：若踩中军旗则斩首获胜！</em></li>
                    <li><strong>地雷 (Q 与 J 阵地防御)</strong>：严禁移动。非工兵单位进攻地雷必被炸死；仅工兵可安全拆除并缴获地雷。</li>
                    <li><strong>正规军官 (10 至 2 级军官)</strong>：点数大吃小 (10 > 9 > 8 > ... > 2)。同级拼杀同归于尽。全部可歼灭工兵。</li>
                    <li><strong>主力工兵 (A 排雷先锋)</strong>：唯一能排雷并俘获地雷的正规军。能击杀敌方战俘动员兵。同级主力工兵相遇同归于尽。不敌 2 至 10 级军官。</li>
                    <li><strong>战俘工兵 (动员兵)</strong>：任何俘获的敌方棋子，重新部署后全权充当<strong>工兵</strong>（可排雷、夺旗）。因受原阵营叛国处决法则制裁，在军阶中为<strong>全场最小棋子</strong>：不敌主力工兵及所有军官；两名战俘工兵相遇时双双同归于尽，直接送入墓地且永不可再次招降。</li>
                </ul>

                <h3 style="color:#d4af37; font-size:1.05rem; margin-bottom:8px;">行动规则与战俘空降</h3>
                <p style="margin-bottom:8px;">每回合玩家二选一执行：<strong>移动1格 (正交上下左右)</strong> 或 <strong>空降1名手牌兵力</strong>。</p>
                <ul style="margin-left:20px; margin-bottom:14px; line-height:1.7;">
                    <li><strong>预备队 (暗置)</strong>：开局秘密保留的2张底牌，空降时暗置进驻，保留其真正面值。</li>
                    <li><strong>战俘工兵 (明置)</strong>：俘获敌兵后空降，必须明置进驻，全权履行工兵职责。</li>
                    <li><strong>空降区域限制</strong>：部队只能空降部署至本方5×5大营空位 (红方1–5排，黑方8–12排)。</li>
                </ul>

                <h3 style="color:#d4af37; font-size:1.05rem; margin-bottom:8px;">兵变法则与叛军处决 (Anti-Mutiny & Treason Rules)</h3>
                <p style="line-height:1.6; background:rgba(0,0,0,0.3); padding:10px; border-left:3px solid #d4af37; border-radius:4px; margin-bottom:14px;">
                    “战俘数量不可超越本军主力！”<br>
                    玩家所拥有的战俘总数 (手牌 + 棋盘明置战俘) <strong>不可超过本方存活的主力部队数</strong>。若俘获敌兵时超过上限，多余战俘直接处决移入墓地；若主力受损失衡，超额战俘将发生溃散。<br><br>
                    <strong>叛军处决法则 (不可二次招降)</strong>：投敌成为动员兵（战俘工兵）的部队一旦在战斗中阵亡或被敌方军官击败，视作叛徒就地处决，<strong>直接移入阵亡墓地，不可被二次招降</strong>。
                </p>

                <h3 style="color:#d4af37; font-size:1.05rem; margin-bottom:8px;">人机难度设定 (CPU Difficulty Levels)</h3>
                <ul style="margin-left:20px; margin-bottom:14px; line-height:1.7;">
                    <li><strong>初级 (Low)</strong>：基础行军与随机进攻，适合新手熟悉规则与基本走法。</li>
                    <li><strong>中级 (Medium)</strong>：具备战术评估能力，懂得保护司令部与优先歼灭工兵。</li>
                    <li><strong>高级 (High)</strong>：深度局势评估，精准掌控兵变平衡、战俘空降与前沿突破。</li>
                </ul>

                <h3 style="color:#d4af37; font-size:1.05rem; margin-bottom:8px;">对战模式说明 (Game Modes)</h3>
                <ul style="margin-left:20px; margin-bottom:14px; line-height:1.7;">
                    <li><strong>1v1 (双人对决)</strong>：经典红黑双雄争霸，5×5本营对决，首破军旗或全歼敌军者胜。</li>
                    <li><strong>2v2 (四人组队)</strong>：四国争霸跨字型十字大棋盘，同花色阵营结盟（梅花盟 vs 红桃盟），歼灭敌方全盟军旗即获胜。</li>
                    <li><strong>1v1v1v1 (四人混战)</strong>：各自为战，4名大将独立统军，最后幸存的唯一指挥官登顶获胜。</li>
                </ul>
            `;
        } else {
            rulebookContentEl.innerHTML = `
                <h3 style="color:#d4af37; font-size:1.05rem; margin-bottom:8px;">Card Roles & Combat Hierarchy</h3>
                <ul style="margin-left:20px; margin-bottom:14px; line-height:1.7;">
                    <li><strong>Flag (Joker)</strong>: Immobile & Defenseless. Any piece stepping onto the Flag captures it for an immediate victory!</li>
                    <li><strong>Bomb (King / K)</strong>: Moves 1 step orthogonally. Mutual destruction with any piece (both sent to Graveyard). <em>Exception: Stepping on Flag captures it to win!</em></li>
                    <li><strong>Landmine (Q & J)</strong>: Strictly immobile. Destroys any non-Sapper that attacks it. Disarmed only by Sappers.</li>
                    <li><strong>Officers (10 down to 2)</strong>: Higher rank captures lower (10 > 9 > ... > 2). Identical ranks destroy each other. All beat Sappers.</li>
                    <li><strong>Native Sapper (Ace / A)</strong>: Disarms and captures Landmines (Q, J). Defeats Conscript Sappers. Mutual destruction with other Native Sappers. Loses to all Officers (2–10). Can capture Flag.</li>
                    <li><strong>Conscript Sapper (Mochigoma)</strong>: Any captured card deployed into play acts strictly as a <strong>Sapper</strong> (disarms landmines, captures flags). Due to betrayal execution by its original side, it is technically the <strong>smallest card</strong> in combat hierarchy: defeated by Native Sappers (A) and all Officers (2–10). When two Conscripts clash, both are executed to the Graveyard together (cannot be re-conscripted).</li>
                </ul>

                <h3 style="color:#d4af37; font-size:1.05rem; margin-bottom:8px;">Turn Actions & Drops</h3>
                <p style="margin-bottom:8px;">Each turn choose exactly one: <strong>Move 1 piece (1 step orthogonal)</strong> OR <strong>Drop 1 card</strong> into your Home Camp.</p>
                <ul style="margin-left:20px; margin-bottom:14px; line-height:1.7;">
                    <li><strong>Reserves (Face-Down)</strong>: Deployed secretly with original true rank intact.</li>
                    <li><strong>Captured Conscripts (Face-Up)</strong>: Deployed face-up as active Sappers.</li>
                    <li><strong>Drop Zone</strong>: Allowed only on unoccupied tiles within your home camp (Ranks 1–5 for Red; Ranks 8–12 for Black).</li>
                </ul>

                <h3 style="color:#d4af37; font-size:1.05rem; margin-bottom:8px;">Anti-Mutiny & Treason Execution Rules</h3>
                <p style="line-height:1.6; background:rgba(0,0,0,0.3); padding:10px; border-left:3px solid #d4af37; border-radius:4px; margin-bottom:14px;">
                    “Your conscript prisoners can never outnumber your loyal forces!”<br>
                    Total Mochigoma count (in hand + active on board) <strong>must not exceed surviving native troops</strong>. Excess captured cards are permanently discarded to the Graveyard.<br><br>
                    <strong>No Re-Conscription (Treason Execution)</strong>: Deployed Conscripts (Mochigoma Sappers) cannot be captured again or "re-conscripted". When defeated or captured by an enemy officer, they are executed on the spot as traitors and sent permanently to the Graveyard.
                </p>

                <h3 style="color:#d4af37; font-size:1.05rem; margin-bottom:8px;">CPU Difficulty Levels</h3>
                <ul style="margin-left:20px; margin-bottom:14px; line-height:1.7;">
                    <li><strong>Low</strong>: Basic movement and opportunistic attacks, ideal for learning the rules.</li>
                    <li><strong>Medium</strong>: Tactical evaluation with flag defense and sapper prioritization.</li>
                    <li><strong>High</strong>: Advanced heuristic scoring, strict anti-mutiny optimization, and aggressive drops.</li>
                </ul>

                <h3 style="color:#d4af37; font-size:1.05rem; margin-bottom:8px;">Game Modes</h3>
                <ul style="margin-left:20px; margin-bottom:14px; line-height:1.7;">
                    <li><strong>1v1 (Duel)</strong>: Classic Red vs Black clash across the frontline. Capture the enemy Flag to win.</li>
                    <li><strong>2v2 (Team Battle)</strong>: 4-player cross-board battle. Players ally by suit (Clubs vs Hearts). Defeat both enemy flags to win.</li>
                    <li><strong>1v1v1v1 (Free-for-All)</strong>: 4 commanders battle independently. Last surviving army wins.</li>
                </ul>
            `;
        }
    }

    // Main Render Function
    function render() {
        const isSetup = game.gameState === 'setup';
        updateAllLocalizedText();

        // Hide unnecessary status & mutiny bar during deployment phase
        if (statusBarEl) statusBarEl.style.display = isSetup ? 'none' : 'flex';
        setupToolbarEl.style.display = isSetup ? 'flex' : 'none';
        setupUnplacedSectionEl.style.display = isSetup ? 'flex' : 'none';

        // Hide Conscripts and Graveyard sections during deployment phase
        if (p1MochigomaSectionEl) p1MochigomaSectionEl.style.display = isSetup ? 'none' : 'flex';
        if (p2MochigomaSectionEl) p2MochigomaSectionEl.style.display = isSetup ? 'none' : 'flex';
        if (graveyardSectionEl) graveyardSectionEl.style.display = isSetup ? 'none' : 'flex';

        if (isSetup) {
            const player = game.setupPlayer;
            const validation = game.validateSetup(player);

            if (uiDeployPhaseLabel) {
                uiDeployPhaseLabel.textContent = (player === 'red' ? 
                    window.I18N.t('setup_turn_red') : 
                    window.I18N.t('setup_turn_black')) + ':';
            }

            setupCampCountEl.textContent = `${validation.placedCount}/25`;
            setupCampCountEl.style.color = validation.placedCount === 25 ? '#2ecc71' : '#f39c12';

            setupReserveCountEl.textContent = `${validation.reserveCount}/2`;
            setupReserveCountEl.style.color = validation.reserveCount === 2 ? '#2ecc71' : '#f39c12';

            setupUnplacedCountEl.textContent = `${validation.unplacedCount}`;
            setupUnplacedCountEl.style.color = validation.unplacedCount === 0 ? '#2ecc71' : '#ff7675';

            if (validation.valid) {
                setupStatusMessageEl.textContent = window.I18N.t('formation_ready');
                setupStatusMessageEl.style.color = '#2ecc71';
                setupConfirmBtn.style.opacity = '1';
            } else {
                setupStatusMessageEl.textContent = validation.errors[0] || '';
                setupStatusMessageEl.style.color = '#ff6b6b';
            }

            renderUnplacedTray(player);
        } else {
            if (game.playerCount === 4) {
                const teamColor = game.seating[game.currentTurn] === 'red' ? 'turn-red' : 'turn-black';
                turnDisplayEl.className = `turn-pill ${teamColor}`;
                turnDisplayEl.textContent = window.I18N.t(`turn_gen_${game.currentTurn}`);
            } else {
                turnDisplayEl.className = `turn-pill ${game.currentTurn === 'red' ? 'turn-red' : 'turn-black'}`;
                turnDisplayEl.textContent = game.currentTurn === 'red' ? 
                    window.I18N.t('turn_red') : 
                    window.I18N.t('turn_black');
            }
        }

        // Mutiny Caps
        const capsContainer = document.getElementById('mutinyCaps') || statusBarEl.querySelector('.mutiny-caps');
        if (capsContainer) {
            capsContainer.innerHTML = '';
            if (game.playerCount === 4) {
                ['a', 'b', 'c', 'd'].forEach(p => {
                    const counts = game.getCounts(p);
                    const isElim = game.eliminated[p];
                    const team = game.seating[p];
                    const badge = document.createElement('div');
                    badge.className = 'cap-badge';
                    if (isElim) badge.style.opacity = '0.35';
                    const pTitle = window.I18N.t(`gen_${p}`);
                    const dotClass = team === 'red' ? 'dot-red' : 'dot-black';
                    badge.innerHTML = `
                        <span><span class="cap-dot ${dotClass}"></span> <strong>${pTitle}</strong>:</span>
                        ${isElim ? '<span style="color:#ff6b6b; font-weight:bold;">[ELIMINATED]</span>' : `
                            <strong>${counts.native}</strong> ${window.I18N.t('native')} |
                            <strong>${counts.mochigoma}</strong> ${window.I18N.t('mochigoma')} |
                            <span>${window.I18N.t('cap')}: <strong>${counts.native}</strong></span>
                        `}
                    `;
                    capsContainer.appendChild(badge);
                });
            } else {
                // 1v1 play: Strictly Red & Black only! Never show 4 players!
                const rCounts = game.getCounts('red');
                const bCounts = game.getCounts('black');
                const redBadge = document.createElement('div');
                redBadge.className = 'cap-badge';
                redBadge.innerHTML = `
                    <span><span class="cap-dot dot-red"></span> <strong>${window.I18N.t('red_army')}</strong></span>
                    <strong>${rCounts.native}</strong> ${window.I18N.t('native')} |
                    <strong>${rCounts.mochigoma}</strong> ${window.I18N.t('mochigoma')} |
                    <span>${window.I18N.t('cap')}: <strong>${rCounts.native}</strong></span>
                `;
                const blackBadge = document.createElement('div');
                blackBadge.className = 'cap-badge';
                blackBadge.innerHTML = `
                    <span><span class="cap-dot dot-black"></span> <strong>${window.I18N.t('black_army')}</strong></span>
                    <strong>${bCounts.native}</strong> ${window.I18N.t('native')} |
                    <strong>${bCounts.mochigoma}</strong> ${window.I18N.t('mochigoma')} |
                    <span>${window.I18N.t('cap')}: <strong>${bCounts.native}</strong></span>
                `;
                capsContainer.appendChild(redBadge);
                capsContainer.appendChild(blackBadge);
            }
        }

        // Render Board
        boardEl.innerHTML = '';
        let legalMoves = [];
        let legalDrops = [];

        if (!isSetup) {
            if (game.selectedTile) {
                legalMoves = game.getLegalMoves(game.selectedTile.r, game.selectedTile.c);
            } else if (game.selectedHandCard) {
                legalDrops = game.getLegalDrops(null, game.selectedHandCard.card);
            }
        }

        if (game.playerCount === 4) {
            boardEl.classList.add('grid-4p');
            for (let r = 0; r < 15; r++) {
                for (let c = 0; c < 15; c++) {
                    const tile = document.createElement('div');
                    tile.className = 'tile';

                    if (!game.isPlayable(r, c)) {
                        if ((r === 6 || r === 8) && (c === 6 || c === 8)) {
                            tile.classList.add('tile-obstacle');
                            tile.innerHTML = `<span class="obstacle-icon" title="Obstacle / 障碍禁行区">${UI_ICONS.obstacle}</span>`;
                        } else {
                            tile.classList.add('tile-void');
                        }
                        boardEl.appendChild(tile);
                        continue;
                    }

                    // Zone backgrounds
                    if (r <= 4) tile.classList.add('tile-camp-a');
                    else if (r >= 10) tile.classList.add('tile-camp-c');
                    else if (c <= 4) tile.classList.add('tile-camp-b');
                    else if (c >= 10) tile.classList.add('tile-camp-d');
                    else tile.classList.add('tile-center');

                    // Frontline markers: 1a..5a, 1b..5b, 1c..5c, 1d..5d
                    if (r === 4 && c >= 5 && c <= 9) {
                        tile.classList.add('frontline-4p');
                        tile.setAttribute('data-fl-label', `${c - 4}a`);
                    } else if (r === 10 && c >= 5 && c <= 9) {
                        tile.classList.add('frontline-4p');
                        tile.setAttribute('data-fl-label', `${c - 4}c`);
                    } else if (c === 4 && r >= 5 && r <= 9) {
                        tile.classList.add('frontline-4p');
                        tile.setAttribute('data-fl-label', `${r - 4}b`);
                    } else if (c === 10 && r >= 5 && r <= 9) {
                        tile.classList.add('frontline-4p');
                        tile.setAttribute('data-fl-label', `${r - 4}d`);
                    }

                    if (game.selectedTile && game.selectedTile.r === r && game.selectedTile.c === c) {
                        tile.classList.add('selected');
                    }

                    const card = game.board[r][c];
                    if (isSetup && card) {
                        if (game.isFrontline(card.player, r, c) && card.isImmobile) {
                            tile.classList.add('invalid-frontline');
                        }
                    }

                    if (!isSetup) {
                        const isLegalMove = legalMoves.some(m => m.r === r && m.c === c);
                        if (isLegalMove) {
                            const target = game.board[r][c];
                            if (target) tile.classList.add('legal-attack');
                            else tile.classList.add('legal-move');
                        }

                        const isLegalDrop = legalDrops.some(d => d.r === r && d.c === c);
                        if (isLegalDrop) tile.classList.add('legal-drop');
                    }

                    if (card) {
                        tile.appendChild(createCardElement(card, r, c, isSetup));
                    }

                    tile.addEventListener('click', () => handleTileClick(r, c));
                    boardEl.appendChild(tile);
                }
            }
        } else {
            boardEl.classList.remove('grid-4p');
            const frontRowRed = 4;
            const frontRowBlack = 7;

            for (let r = 11; r >= 0; r--) {
                for (let c = 0; c < 5; c++) {
                    const tile = document.createElement('div');
                    tile.className = 'tile';
                    tile.setAttribute('data-r', r);
                    tile.setAttribute('data-c', c);
                    if (r === 5 || r === 6) tile.classList.add('frontline');

                    if (game.selectedTile && game.selectedTile.r === r && game.selectedTile.c === c) {
                        tile.classList.add('selected');
                    }

                    const card = game.board[r][c];
                    if (isSetup && card) {
                        if ((r === frontRowRed || r === frontRowBlack) && card.isImmobile) {
                            tile.classList.add('invalid-frontline');
                        }
                    }

                    if (!isSetup) {
                        const isLegalMove = legalMoves.some(m => m.r === r && m.c === c);
                        if (isLegalMove) {
                            const target = game.board[r][c];
                            if (target) {
                                tile.classList.add('legal-attack');
                            } else {
                                tile.classList.add('legal-move');
                            }
                        }

                        const isLegalDrop = legalDrops.some(d => d.r === r && d.c === c);
                        if (isLegalDrop) {
                            tile.classList.add('legal-drop');
                        }
                    }

                    if (card) {
                        tile.appendChild(createCardElement(card, r, c, isSetup));
                    }

                    tile.addEventListener('click', () => handleTileClick(r, c));
                    boardEl.appendChild(tile);
                }
            }
        }

        // Render Hands
        if (game.playerCount === 4) {
            const activeP = game.currentTurn;
            const pTitle = window.I18N.t(`gen_${activeP}`);
            document.getElementById('uiP1StartingHeader').textContent = `${pTitle} ${window.I18N.t('reserves')}`;
            document.getElementById('uiP1MochiHeader').textContent = `${pTitle} ${window.I18N.t('mochigoma')}`;
            renderHandTray(p1StartingTrayEl, game.hands[activeP].startingReserves, activeP, 'starting', isSetup);
            renderHandTray(p1MochigomaTrayEl, game.hands[activeP].mochigoma, activeP, 'mochigoma', isSetup);
            p2StartingTrayEl.innerHTML = '';
            p2MochigomaTrayEl.innerHTML = '';
        } else {
            document.getElementById('uiP1StartingHeader').textContent = window.I18N.t('p1_starting_reserve');
            document.getElementById('uiP1MochiHeader').textContent = window.I18N.t('p1_mochigoma');
            renderHandTray(p1StartingTrayEl, game.hands.red.startingReserves, 'red', 'starting', isSetup);
            renderHandTray(p1MochigomaTrayEl, game.hands.red.mochigoma, 'red', 'mochigoma', isSetup);
            renderHandTray(p2StartingTrayEl, game.hands.black.startingReserves, 'black', 'starting', isSetup);
            renderHandTray(p2MochigomaTrayEl, game.hands.black.mochigoma, 'black', 'mochigoma', isSetup);
        }

        // Render Graveyard with Click-to-Inspect
        graveyardListEl.innerHTML = '';
        game.graveyard.forEach(card => {
            const span = document.createElement('span');
            span.className = card.originalOwner === 'red' ? 'log-entry red' : 'log-entry black';
            span.style.cursor = 'pointer';
            span.style.padding = '1px 4px';
            span.style.borderRadius = '3px';
            span.style.background = 'rgba(0,0,0,0.25)';
            span.title = window.I18N.t('inspect_hint');
            const disp = card.isFlag ? '★' : card.rank;
            span.textContent = `${disp} `;
            span.addEventListener('click', () => showCardInspect(card));
            graveyardListEl.appendChild(span);
        });

        // Trigger Clash Modal only when fresh
        if (game.lastClashResult && (!activeClash || game.lastClashResult.id !== activeClash.id)) {
            activeClash = game.lastClashResult;
            showClashModal(activeClash);
        }

        // Check Game Over
        if (game.gameState === 'gameover' && clashModalEl.style.display !== 'flex') {
            setTimeout(() => {
                showGameOver(game.winReason);
            }, 100);
        }
    }

    // Card DOM with NO tautology in role name!
    function createCardElement(card, r, c, isSetup = false) {
        const cardDiv = document.createElement('div');
        const teamColor = (card.team === 'red' || card.player === 'red' || card.player === 'a' || card.player === 'c') ? 'red-side' : 'black-side';
        cardDiv.className = `card-unit ${teamColor}`;

        const isSettingUpThisCard = isSetup && card.player === game.setupPlayer;
        const revealInPvE = (game.mode === 'pve' || game.mode === 'online') && card.player === game.humanSide;
        const revealInSandbox = game.mode === 'sandbox';

        const shouldShow = isSettingUpThisCard || card.faceUp || revealInPvE || revealInSandbox;

        if (card.isMochigoma) {
            cardDiv.classList.add('mochigoma-sapper');
            cardDiv.setAttribute('data-badge-text', window.I18N.t('badge_conscript'));
        }

        if (shouldShow) {
            cardDiv.classList.add('face-up');
            const origColor = (card.originalOwner === 'red' || card.team === 'red' || card.player === 'a' || card.player === 'c') ? 'red-card' : 'black-card';
            cardDiv.classList.add(origColor);

            if (window.I18N.currentCardStyle === 'art') {
                cardDiv.classList.add('art-half-card');
                cardDiv.innerHTML = getHalfArtCardHTML(card);
            } else {
                cardDiv.classList.add('simplified-mode-unit');
                cardDiv.innerHTML = getSimplifiedCardHTML(card);
            }
        } else {
            cardDiv.classList.add('face-down');
            if (window.I18N.currentCardStyle === 'art') {
                cardDiv.classList.add('art-half-card');
            }
        }

        if (!isSetup && card.player === game.currentTurn && !card.isImmobile && typeof r === 'number' && typeof c === 'number') {
            const isMyTurnOnline = (window.networkClient && window.networkClient.isOnlineMatch) ? (card.player === window.networkClient.playerColor) : true;
            if (isMyTurnOnline) {
                const moves = game.getLegalMoves(r, c);
                if (moves && moves.length > 0) {
                    cardDiv.classList.add('can-move');
                }
            }
        }

        if (game.playerCount === 4) {
            const badgeEl = document.createElement('span');
            badgeEl.className = `player-badge-pill badge-${card.player}`;
            badgeEl.textContent = card.player.toUpperCase();
            cardDiv.appendChild(badgeEl);
        }

        return cardDiv;
    }

    function renderUnplacedTray(player) {
        unplacedTrayEl.innerHTML = '';

        // If a reserve card is selected, clicking the unplaced tray returns it to unplaced!
        unplacedTrayEl.onclick = (e) => {
            if (game.selectedHandCard && game.selectedHandCard.type === 'starting') {
                const card = game.hands[game.setupPlayer].startingReserves.splice(game.selectedHandCard.index, 1)[0];
                game.unplacedCards[game.setupPlayer].push(card);
                game.selectedHandCard = null;
                window.soundFX.playCardFlip();
                render();
            }
        };

        game.unplacedCards[player].forEach((card, idx) => {
            const cardDiv = document.createElement('div');
            cardDiv.className = `card-unit face-up ${card.originalOwner === 'red' ? 'red-card' : 'black-card'}`;

            if (game.selectedUnplacedIndex === idx) {
                cardDiv.style.outline = '2px solid var(--gold)';
            }

            if (window.I18N.currentCardStyle === 'art') {
                cardDiv.classList.add('art-half-card');
                cardDiv.innerHTML = getHalfArtCardHTML(card);
            } else {
                cardDiv.classList.add('simplified-mode-unit');
                cardDiv.innerHTML = getSimplifiedCardHTML(card);
            }

            cardDiv.addEventListener('click', (e) => {
                e.stopPropagation();

                // If a reserve card is selected, clicking an unplaced card swaps them!
                if (game.selectedHandCard && game.selectedHandCard.type === 'starting') {
                    const reserveCard = game.hands[game.setupPlayer].startingReserves.splice(game.selectedHandCard.index, 1)[0];
                    const unplacedCard = game.unplacedCards[player].splice(idx, 1)[0];
                    game.hands[game.setupPlayer].startingReserves.push(unplacedCard);
                    game.unplacedCards[player].push(reserveCard);
                    game.selectedHandCard = null;
                    window.soundFX.playCardFlip();
                    render();
                    return;
                }

                game.selectedTile = null;
                game.selectedHandCard = null;
                game.selectedUnplacedIndex = game.selectedUnplacedIndex === idx ? null : idx;
                render();
            });

            unplacedTrayEl.appendChild(cardDiv);
        });
    }

    function renderHandTray(container, cards, player, type, isSetup = false) {
        container.innerHTML = '';

        // SPECIAL SETUP RESERVE FRAME: 2 dedicated slots with direct placement
        const isThisSetupReserve = isSetup && (type === 'starting') && (player === game.setupPlayer);
        const hasSelectionToReserve = isThisSetupReserve && (
            (game.selectedUnplacedIndex !== null) || 
            (game.selectedTile !== null && game.board[game.selectedTile.r][game.selectedTile.c] && game.board[game.selectedTile.r][game.selectedTile.c].player === player)
        );

        if (isThisSetupReserve) {
            container.classList.add('setup-reserve-frame');
            if (hasSelectionToReserve) {
                container.classList.add('can-drop-reserve');
            } else {
                container.classList.remove('can-drop-reserve');
            }

            container.onclick = (e) => {
                if (hasSelectionToReserve) {
                    handlePutCardIntoReserve(player);
                }
            };

            for (let slotIdx = 0; slotIdx < 2; slotIdx++) {
                const card = cards[slotIdx];
                if (card) {
                    const cardDiv = document.createElement('div');
                    cardDiv.className = `card-unit face-up ${card.originalOwner === 'red' ? 'red-card' : 'black-card'}`;
                    if (window.I18N.currentCardStyle === 'art') {
                        cardDiv.classList.add('art-half-card');
                        cardDiv.innerHTML = getHalfArtCardHTML(card);
                    } else {
                        cardDiv.classList.add('simplified-mode-unit');
                        cardDiv.innerHTML = getSimplifiedCardHTML(card, type);
                    }

                    const isSelected = game.selectedHandCard && 
                                       game.selectedHandCard.player === player && 
                                       game.selectedHandCard.type === type && 
                                       game.selectedHandCard.index === slotIdx;
                    if (isSelected) cardDiv.style.outline = '2px solid var(--gold)';

                    cardDiv.addEventListener('click', (e) => {
                        e.stopPropagation();
                        if (hasSelectionToReserve) {
                            handlePutCardIntoReserve(player, slotIdx);
                        } else {
                            game.selectedTile = null;
                            game.selectedUnplacedIndex = null;
                            game.selectedHandCard = isSelected ? null : { player, type, index: slotIdx, card };
                            render();
                        }
                    });
                    container.appendChild(cardDiv);
                } else {
                    // Empty reserve slot - direct drop target!
                    const emptySlot = document.createElement('div');
                    emptySlot.className = `reserve-slot empty-slot ${hasSelectionToReserve ? 'has-selection' : ''}`;
                    const slotLabel = window.I18N && window.I18N.currentLang === 'zh' ? `预备位 ${slotIdx + 1}` : `Reserve ${slotIdx + 1}`;
                    emptySlot.innerHTML = `
                        ${UI_ICONS.dropSlot}
                        <div>${slotLabel}</div>
                    `;
                    emptySlot.addEventListener('click', (e) => {
                        e.stopPropagation();
                        if (hasSelectionToReserve) {
                            handlePutCardIntoReserve(player, slotIdx);
                        }
                    });
                    container.appendChild(emptySlot);
                }
            }
            return;
        } else {
            container.classList.remove('setup-reserve-frame', 'can-drop-reserve');
            container.onclick = null;
        }

        cards.forEach((card, idx) => {
            const cardDiv = document.createElement('div');

            // Visibility determination: Reserves are secret face-down to the opponent!
            let isVisible = false;
            if (type === 'mochigoma') {
                isVisible = true; // Conscripts are public knowledge
            } else {
                // Reserve cards: only visible to the owner
                const isSettingUpThis = isSetup && (player === game.setupPlayer);
                const isMyTurnInPvP = (game.mode === 'pvp' && player === game.currentTurn);
                const isHumanInPvE = ((game.mode === 'pve' || game.mode === 'online') && player === game.humanSide);
                const isSandbox = (game.mode === 'sandbox');

                isVisible = isSettingUpThis || isSandbox || isHumanInPvE || (isMyTurnInPvP && !isSetup);
            }

            const isSelected = game.selectedHandCard && 
                               game.selectedHandCard.player === player && 
                               game.selectedHandCard.type === type && 
                               game.selectedHandCard.index === idx;

            if (isVisible) {
                cardDiv.className = `card-unit face-up ${card.originalOwner === 'red' ? 'red-card' : 'black-card'}`;
                if (type === 'mochigoma') {
                    cardDiv.classList.add('mochigoma-sapper');
                    cardDiv.setAttribute('data-badge-text', window.I18N.t('badge_conscript'));
                }

                if (window.I18N.currentCardStyle === 'art') {
                    cardDiv.classList.add('art-half-card');
                    cardDiv.innerHTML = getHalfArtCardHTML(card);
                } else {
                    cardDiv.classList.add('simplified-mode-unit');
                    cardDiv.innerHTML = getSimplifiedCardHTML(card, type);
                }
            } else {
                // Secret face-down card!
                cardDiv.className = `card-unit face-down ${card.player === 'red' ? 'red-side' : 'black-side'}`;
                if (window.I18N.currentCardStyle === 'art') {
                    cardDiv.classList.add('art-half-card');
                }
            }

            if (isSelected) cardDiv.style.outline = '2px solid var(--gold)';

            cardDiv.addEventListener('click', (e) => {
                e.stopPropagation();
                if (isSetup) {
                    if (player !== game.setupPlayer) return;
                    game.selectedTile = null;
                    game.selectedUnplacedIndex = null;
                    game.selectedHandCard = isSelected ? null : { player, type, index: idx, card };
                    render();
                    return;
                }

                if (game.currentTurn !== player) return;
                if (game.mode === 'pve' && player === game.botSide) return;

                if (isSelected) {
                    game.selectedHandCard = null;
                } else {
                    game.selectedTile = null;
                    game.selectedHandCard = { player, type, index: idx, card };
                }
                render();
            });

            container.appendChild(cardDiv);
        });
    }

    // Helper to generate the role image SVG ONLY for special cards (J, Q, K, Joker)
    function getCardArtSVG(card, isMini = false) {
        const isRed = card.originalOwner === 'red';
        const strokeColor = isRed ? '#a81616' : '#1a1a1a';
        const bodyFill = isRed ? '#800e0e' : '#1c1f24';
        const flagFill = isRed ? '#b81414' : '#1e2430';
        const goldAccent = '#d4af37';
        const svgClass = isMini ? 'half-card-svg' : 'full-card-svg';

        // 1. Joker: Triangular Waving Pennant Flag on Flagpole (per iEmoji 🚩 reference)
        if (card.isFlag) {
            return `
                <svg viewBox="0 0 40 40" class="${svgClass}">
                    <!-- Flagpole with Ball Finial -->
                    <line x1="11" y1="5" x2="11" y2="36" stroke="#9aa5b4" stroke-width="2.2" stroke-linecap="round"/>
                    <circle cx="11" cy="4.5" r="2.6" fill="${goldAccent}" stroke="#8a701a" stroke-width="0.6"/>
                    <!-- Triangular Pennant -->
                    <path d="M11 6.5 C19 4.8, 27 8.5, 35 13.5 C27 18, 19 21.5, 11 23.5 Z" fill="${flagFill}" stroke="${goldAccent}" stroke-width="1.2" stroke-linejoin="round"/>
                    <!-- Waving Fabric Crease / Highlight -->
                    <path d="M11 6.5 C17 5.5, 23 9.5, 26 11.5 C21 16, 16 19.5, 11 23.5" fill="rgba(255, 255, 255, 0.22)"/>
                    <!-- Pole Mounting Collars -->
                    <rect x="9.8" y="6.5" width="2.4" height="1.4" fill="${goldAccent}"/>
                    <rect x="9.8" y="22.5" width="2.4" height="1.4" fill="${goldAccent}"/>
                    <!-- Ground Stand Line -->
                    <line x1="7.5" y1="36" x2="14.5" y2="36" stroke="${goldAccent}" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
            `;
        }

        // 2. King: Spiked Spherical Naval Contact Mine / Water Bomb (per reference image)
        if (card.isBomb) {
            return `
                <svg viewBox="0 0 40 40" class="${svgClass}">
                    <!-- 8 Contact Horns / Spikes (4 Cardinal + 4 Ordinal) -->
                    <g fill="${bodyFill}" stroke="${goldAccent}" stroke-width="1.1" stroke-linejoin="round">
                        <!-- North -->
                        <path d="M18.8 11.5 L18.8 4 C18.8 3.2 21.2 3.2 21.2 4 L21.2 11.5 Z"/>
                        <!-- South -->
                        <path d="M18.8 28.5 L18.8 36 C18.8 36.8 21.2 36.8 21.2 36 L21.2 28.5 Z"/>
                        <!-- West -->
                        <path d="M11.5 18.8 L4 18.8 C3.2 18.8 3.2 21.2 4 21.2 L11.5 21.2 Z"/>
                        <!-- East -->
                        <path d="M28.5 18.8 L36 18.8 C36.8 18.8 36.8 21.2 36 21.2 L28.5 21.2 Z"/>
                        <!-- NW -->
                        <path d="M13.2 13.2 L8 8 C7.3 7.3 9.3 5.3 10 6 L15.2 11.2 Z"/>
                        <!-- NE -->
                        <path d="M26.8 13.2 L32 8 C32.7 7.3 34.7 9.3 34 10 L28.8 15.2 Z"/>
                        <!-- SW -->
                        <path d="M13.2 26.8 L8 32 C7.3 32.7 5.3 30.7 6 30 L11.2 24.8 Z"/>
                        <!-- SE -->
                        <path d="M26.8 26.8 L32 32 C32.7 32.7 30.7 34.7 30 34 L24.8 28.8 Z"/>
                    </g>
                    <!-- Spherical Mine Hull -->
                    <circle cx="20" cy="20" r="9" fill="${bodyFill}" stroke="${goldAccent}" stroke-width="1.3"/>
                    <!-- Specular Highlight Arc -->
                    <path d="M14.5 16 A 6.5 6.5 0 0 1 20 13.5" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.2" stroke-linecap="round"/>
                    <!-- Center Contact Detonator -->
                    <circle cx="20" cy="20" r="2.4" fill="${goldAccent}" stroke="#8a701a" stroke-width="0.5"/>
                    <!-- Perimeter Contact Studs / Rivets -->
                    <circle cx="16" cy="16" r="1.3" fill="${goldAccent}"/>
                    <circle cx="24" cy="16" r="1.3" fill="${goldAccent}"/>
                    <circle cx="16" cy="24" r="1.3" fill="${goldAccent}"/>
                    <circle cx="24" cy="24" r="1.3" fill="${goldAccent}"/>
                </svg>
            `;
        }

        // 3. Landmines: Queen (Q) & Jack (J) - Cylindrical Disc Pressure Mine with Shockwave Sparks
        if (card.isLandmine) {
            return `
                <svg viewBox="0 0 44 32" class="${svgClass}">
                    <!-- Shockwave / Lightning Sparks Top-Left -->
                    <path d="M7 6 L11 11 L9 12 L14 15" fill="none" stroke="${goldAccent}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                    <line x1="12" y1="4.5" x2="13.5" y2="7.5" stroke="${goldAccent}" stroke-width="1.2" stroke-linecap="round"/>
                    <line x1="4.5" y1="9.5" x2="7" y2="12" stroke="${goldAccent}" stroke-width="1.2" stroke-linecap="round"/>

                    <!-- Shockwave / Lightning Sparks Top-Right -->
                    <path d="M37 6 L33 11 L35 12 L30 15" fill="none" stroke="${goldAccent}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                    <line x1="32" y1="4.5" x2="30.5" y2="7.5" stroke="${goldAccent}" stroke-width="1.2" stroke-linecap="round"/>
                    <line x1="39.5" y1="9.5" x2="37" y2="12" stroke="${goldAccent}" stroke-width="1.2" stroke-linecap="round"/>

                    <!-- Cylindrical Lower Base -->
                    <path d="M12 20 L12 24.5 C12 28.5, 32 28.5, 32 24.5 L32 20 Z" fill="${bodyFill}" stroke="${goldAccent}" stroke-width="1.1"/>

                    <!-- Disc Upper Bevel & Pressure Plate Surface -->
                    <ellipse cx="22" cy="19.5" rx="11" ry="4.2" fill="${strokeColor}" stroke="${goldAccent}" stroke-width="1.2"/>

                    <!-- Central Pressure Button / Detonator -->
                    <ellipse cx="22" cy="18.5" rx="5" ry="2" fill="${goldAccent}" stroke="#8a701a" stroke-width="0.6"/>
                    <circle cx="22" cy="18" r="1.2" fill="${isRed ? '#ff4d4d' : '#d4af37'}"/>

                    <!-- Radial Grip Grooves -->
                    <line x1="15" y1="18.5" x2="17.5" y2="19.5" stroke="${goldAccent}" stroke-width="1" stroke-linecap="round"/>
                    <line x1="29" y1="18.5" x2="26.5" y2="19.5" stroke="${goldAccent}" stroke-width="1" stroke-linecap="round"/>
                </svg>
            `;
        }

        // 4. 1 to 10 cards (A, 2..10): CLEAR without any design in the middle!
        return '';
    }

    // Simplified Mode Card Renderer
    // 1. Number cards (A, 2..10): Delete all words and image.
    // 2. Court cards (J, Q, K): Keep the words (Landmine / Bomb).
    // 3. Joker (Flag): Use the flag image in art mode.
    function getSimplifiedCardHTML(card, type = null) {
        const isMochi = card.isMochigoma || type === 'mochigoma';
        const cleanRole = isMochi ? window.I18N.t('role_conscript') : card.getRoleName();

        // 1. Joker: Flag image from art mode!
        if (card.isFlag) {
            const flagSvg = getCardArtSVG(card, true);
            return `
                <div class="card-top">
                    <span class="sim-rank joker-text">JOKER</span>
                    <span class="sim-suit"></span>
                </div>
                <div class="card-center-flag">
                    ${flagSvg}
                </div>
            `;
        }

        // 2. J, Q, K: Keep the words! (In simplified mode, landmines display as "Mine")
        if (card.isBomb || card.isLandmine) {
            let roleDisplay = cleanRole;
            if (card.isLandmine) {
                roleDisplay = (window.I18N && window.I18N.currentLang === 'zh') ? '地雷' : 'Mine';
            }
            return `
                <div class="card-top">
                    <span class="sim-rank">${card.rank}</span>
                    <span class="sim-suit">${card.suit}</span>
                </div>
                <div class="card-center-space"></div>
                <div class="card-sub-role">${roleDisplay}</div>
            `;
        }

        // 3. Number cards (A, 2..10): Delete all words and image!
        return `
            <div class="card-top">
                <span class="sim-rank">${card.rank}</span>
                <span class="sim-suit">${card.suit}</span>
            </div>
            <div class="card-body-empty"></div>
        `;
    }

    // Simplified Mode Clash Card Renderer
    function getSimplifiedClashCardHTML(card, label) {
        const isMochi = card.isMochigoma;
        let cleanRole = isMochi ? window.I18N.t('role_conscript') : ((typeof card.getRoleName === 'function') ? card.getRoleName() : (card.roleName || 'Officer'));
        if (card.isLandmine) {
            cleanRole = (window.I18N && window.I18N.currentLang === 'zh') ? '地雷' : 'Mine';
        }
        const showRole = (card.isBomb || card.isLandmine);
        const flagSvg = card.isFlag ? getCardArtSVG(card, false) : '';

        return `
            <div class="card-unit face-up ${card.originalOwner === 'red' ? 'red-card' : 'black-card'}" style="width:110px; height:150px; padding:10px; display:flex; flex-direction:column; justify-content:space-between; box-sizing:border-box;">
                <div style="font-size:0.75rem; font-weight:800; color:#888;">${label} (${card.player.toUpperCase()})</div>
                ${card.isFlag ? `
                    <div style="flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                        <div style="font-size:1.1rem; font-weight:900; margin-bottom:4px;">JOKER</div>
                        <div style="width:52px; height:52px; display:flex; align-items:center; justify-content:center;">${flagSvg}</div>
                    </div>
                ` : `
                    <div style="font-size:2.2rem; margin:auto 0; font-family:serif; text-align:center;">${card.suit}${card.rank}</div>
                `}
                <div style="font-size:0.85rem; font-weight:800; text-align:center; min-height:16px;">${showRole ? cleanRole : ''}</div>
            </div>
        `;
    }

    // On-Table & Trays: Symmetrical Top-Half Slice
    function getHalfArtCardHTML(card) {
        const isSpecial = card.isFlag || card.isBomb || card.isLandmine;
        const roleName = (typeof card.getRoleName === 'function') ? card.getRoleName() : (card.roleName || 'Officer');
        const svg = isSpecial ? getCardArtSVG(card, true) : '';

        // Number cards & J, Q, K: Top-left has Rank, Top-right has Suit
        // Jokers: Top-left has "JOKER", Top-right is empty
        const rankLeft = card.isFlag ? 'JOKER' : card.rank;
        const suitRight = card.isFlag ? '' : card.suit;

        return `
            <div class="half-card-header">
                <span class="half-rank ${card.isFlag ? 'joker-text' : ''}">${rankLeft}</span>
                <span class="half-suit-corner">${suitRight}</span>
            </div>
            <div class="half-card-body ${isSpecial ? 'has-special-art' : 'clear-middle'}">
                ${svg}
            </div>
            <div class="half-card-divider">${roleName}</div>
        `;
    }

    // Full-Size 2-Way Symmetric Poker Card (For Clash Reveal & Card Inspection)
    function getFullSizeArtCardHTML(card) {
        const isRed = card.originalOwner === 'red';
        const isSpecial = card.isFlag || card.isBomb || card.isLandmine;
        const roleName = (typeof card.getRoleName === 'function') ? card.getRoleName() : (card.roleName || 'Officer');
        const svg = isSpecial ? getCardArtSVG(card, false) : '';
        const rankLeft = card.isFlag ? 'JOKER' : card.rank;
        const suitRight = card.isFlag ? '' : card.suit;

        return `
            <div class="full-poker-card ${isRed ? 'red-card' : 'black-card'}">
                <div class="full-card-index top-left">
                    <span class="full-rank ${card.isFlag ? 'joker-text' : ''}">${rankLeft}</span>
                    ${suitRight ? `<span class="full-suit">${suitRight}</span>` : ''}
                </div>

                <div class="full-card-center-frame ${isSpecial ? 'has-special-art' : 'clear-middle'}">
                    ${isSpecial ? `
                        <div class="full-figure-top">
                            ${svg}
                        </div>
                        <div class="full-card-midline-bar">
                            ${roleName}
                        </div>
                        <div class="full-figure-bottom">
                            ${svg}
                        </div>
                    ` : `
                        <div class="full-card-midline-bar" style="margin:auto 0;">
                            ${roleName}
                        </div>
                    `}
                </div>

                <div class="full-card-index bottom-right">
                    <span class="full-rank ${card.isFlag ? 'joker-text' : ''}">${rankLeft}</span>
                    ${suitRight ? `<span class="full-suit">${suitRight}</span>` : ''}
                </div>
            </div>
        `;
    }
    function handleTileClick(r, c) {
        const isSetup = game.gameState === 'setup';
        const activeSetupPlayer = game.setupPlayer;

        // SETUP MODE
        if (isSetup) {
            let isInsideCamp = false;
            if (game.playerCount === 4) {
                isInsideCamp = game.getCampCells(activeSetupPlayer).some(pos => pos.r === r && pos.c === c);
            } else {
                const minCampRow = activeSetupPlayer === 'red' ? 0 : 7;
                const maxCampRow = activeSetupPlayer === 'red' ? 4 : 11;
                isInsideCamp = (r >= minCampRow && r <= maxCampRow);
            }

            if (!isInsideCamp) {
                if (game.selectedTile) {
                    showToast(window.I18N ? window.I18N.t('formation_ready_prompt') : 'Formation deployed! Tap Confirm & Battle to begin marching.');
                    if (setupConfirmBtn) {
                        setupConfirmBtn.classList.remove('btn-pulse');
                        void setupConfirmBtn.offsetWidth;
                        setupConfirmBtn.classList.add('btn-pulse');
                    }
                } else {
                    showToast(window.I18N.t('drop_camp_only'));
                }
                return;
            }

            if (game.selectedUnplacedIndex !== null) {
                const unplacedCard = game.unplacedCards[activeSetupPlayer].splice(game.selectedUnplacedIndex, 1)[0];
                const existing = game.board[r][c];
                game.board[r][c] = unplacedCard;
                if (existing) {
                    game.unplacedCards[activeSetupPlayer].push(existing);
                }
                game.selectedUnplacedIndex = null;
                window.soundFX.playCardFlip();
                render();
                return;
            }

            if (game.selectedHandCard && game.selectedHandCard.type === 'starting') {
                const reserveCard = game.hands[activeSetupPlayer].startingReserves.splice(game.selectedHandCard.index, 1)[0];
                const existing = game.board[r][c];
                game.board[r][c] = reserveCard;
                if (existing) {
                    game.hands[activeSetupPlayer].startingReserves.push(existing);
                }
                game.selectedHandCard = null;
                window.soundFX.playCardFlip();
                render();
                return;
            }

            if (game.selectedTile) {
                const fromCard = game.board[game.selectedTile.r][game.selectedTile.c];
                const targetCard = game.board[r][c];

                if (game.selectedTile.r === r && game.selectedTile.c === c) {
                    game.selectedTile = null;
                } else {
                    game.board[r][c] = fromCard;
                    game.board[game.selectedTile.r][game.selectedTile.c] = targetCard;
                    game.selectedTile = null;
                    window.soundFX.playMove();
                }
                render();
                return;
            }

            const cardOnTile = game.board[r][c];
            if (cardOnTile && cardOnTile.player === activeSetupPlayer) {
                game.selectedTile = { r, c };
                render();
                return;
            }

            return;
        }

        // BATTLE MODE
        if (game.gameState !== 'playing') return;
        if (game.mode === 'pve' && game.currentTurn === game.botSide) return;
        if (clashModalEl.style.display === 'flex') return;

        if (game.selectedHandCard) {
            const legalDrops = game.getLegalDrops(null, game.selectedHandCard.card);
            const isValid = legalDrops.some(d => d.r === r && d.c === c);
            if (isValid) {
                if (window.networkClient && window.networkClient.isOnlineMatch) {
                    window.networkClient.sendAction({
                        type: 'drop',
                        handType: game.selectedHandCard.type,
                        index: game.selectedHandCard.index,
                        to: { r, c }
                    });
                    game.selectedHandCard = null;
                    render();
                    return;
                }
                game.dropCard(game.selectedHandCard.type, game.selectedHandCard.index, r, c);
                game.selectedHandCard = null;
                render();
                return;
            }
        }

        if (game.selectedTile) {
            const legalMoves = game.getLegalMoves(game.selectedTile.r, game.selectedTile.c);
            const isMoveValid = legalMoves.some(m => m.r === r && m.c === c);
            if (isMoveValid) {
                if (window.networkClient && window.networkClient.isOnlineMatch) {
                    window.networkClient.sendAction({
                        type: 'move',
                        from: { r: game.selectedTile.r, c: game.selectedTile.c },
                        to: { r, c }
                    });
                    game.selectedTile = null;
                    render();
                    return;
                }
                game.movePiece(game.selectedTile.r, game.selectedTile.c, r, c);
                game.selectedTile = null;
                render();
                return;
            }
        }

        const card = game.board[r][c];
        if (card && card.player === game.currentTurn) {
            if (window.networkClient && window.networkClient.isOnlineMatch && card.player !== window.networkClient.playerColor) {
                return;
            }
            if (card.isImmobile) {
                showToast(window.I18N.t('immobile_alert', { role: card.roleName }));
                return;
            }
            const legalMoves = game.getLegalMoves(r, c);
            if (legalMoves.length === 0) {
                showToast(window.I18N ? window.I18N.t('unit_blocked') : 'Unit is blocked by friendly troops in front. Advance your frontline first!');
            }
            game.selectedHandCard = null;
            game.selectedTile = { r, c };
            render();
            return;
        }

        game.selectedTile = null;
        game.selectedHandCard = null;
        render();
    }

    function getLocalizedClashVerdict(clash) {
        if (!clash) return '';
        const a = (clash.attacker instanceof Card) ? clash.attacker : deserializeCard(clash.attacker, 'red');
        const d = (clash.defender instanceof Card) ? clash.defender : deserializeCard(clash.defender, 'black');
        if (!a || !d) return clash.outcomeText || '';

        if (!window.I18N) return clash.outcomeText || '';

        const isZh = window.I18N.currentLang === 'zh';
        const aName = isZh ? (a.player === 'red' ? '红方' : '黑方') : a.player.toUpperCase();
        const dName = isZh ? (d.player === 'red' ? '红方' : '黑方') : d.player.toUpperCase();

        // 1. Flag Assault
        if (d.isFlag) {
            return a.player === 'red' ? window.I18N.t('win_red') : window.I18N.t('win_black');
        }

        // 2. Bomb Detonations
        if (a.isBomb || d.isBomb) {
            return window.I18N.t('bomb_explosion');
        }

        // 3. Landmine Defense
        if (d.isLandmine) {
            if (a.isSapper || a.isMochigoma) {
                return window.I18N.t('mine_cleared');
            } else {
                const aRole = (typeof a.getRoleName === 'function') ? a.getRoleName() : (a.roleName || 'Officer');
                return window.I18N.t('mine_detonation', { attacker: aRole });
            }
        }

        // 4. Conscript vs Conscript
        if (a.isMochigoma && d.isMochigoma) {
            return window.I18N.t('conscript_clash');
        }

        // 5. Native Sapper vs Native Sapper
        if (a.isSapper && d.isSapper && !a.isMochigoma && !d.isMochigoma) {
            return window.I18N.t('sapper_clash');
        }

        // 6. Native Sapper vs Conscript
        if (a.isSapper && !a.isMochigoma && d.isMochigoma) {
            return window.I18N.t('sapper_executed_conscript', { player: aName });
        }
        if (a.isMochigoma && d.isSapper && !d.isMochigoma) {
            return window.I18N.t('sapper_executed_conscript', { player: dName });
        }

        // 7. Conscript vs Officer
        if (a.isMochigoma) {
            return window.I18N.t('officer_executed_conscript', { player: dName });
        }
        if (d.isMochigoma) {
            return window.I18N.t('officer_executed_conscript', { player: aName });
        }

        // 8. Native Sapper vs Officer
        if (a.isSapper && !a.isMochigoma) {
            return window.I18N.t('officer_captured_sapper', { player: dName });
        }
        if (d.isSapper && !d.isMochigoma) {
            return window.I18N.t('sapper_captured_by_officer', { player: aName });
        }

        // 9. Officer vs Officer
        if (clash.winner === 'attacker') {
            return window.I18N.t('officer_victory', { player: aName });
        } else if (clash.winner === 'defender') {
            return window.I18N.t('officer_defeat', { player: dName });
        } else {
            return window.I18N.t('officer_tie');
        }
    }

    function showClashModal(clash) {
        if (!clash) return;
        clashModalEl.style.display = 'flex';

        const attackerCard = (clash.attacker instanceof Card) ? clash.attacker : deserializeCard(clash.attacker, 'red');
        const defenderCard = (clash.defender instanceof Card) ? clash.defender : deserializeCard(clash.defender, 'black');

        if (window.I18N.currentCardStyle === 'art') {
            clashAttackerEl.innerHTML = getFullSizeArtCardHTML(attackerCard);
            clashDefenderEl.innerHTML = getFullSizeArtCardHTML(defenderCard);
        } else {
            clashAttackerEl.innerHTML = getSimplifiedClashCardHTML(attackerCard, window.I18N.t('clash_attacker'));
            clashDefenderEl.innerHTML = getSimplifiedClashCardHTML(defenderCard, window.I18N.t('clash_defender'));
        }
        const localizedVerdict = getLocalizedClashVerdict(clash) || clash.outcomeText;
        clashVerdictEl.textContent = localizedVerdict;

        if (autoCloseTimer) clearTimeout(autoCloseTimer);
        autoCloseTimer = setTimeout(() => {
            closeClashModal();
        }, 4000);
    }

    function showCardInspect(card) {
        if (!card || !cardInspectModalEl) return;
        inspectTitleEl.textContent = window.I18N.t('inspect_title');
        inspectCardContainerEl.innerHTML = getFullSizeArtCardHTML(card);
        const isZh = window.I18N.currentLang === 'zh';
        const ownerName = card.originalOwner === 'red' ? (isZh ? '红方部队' : 'RED ARMY') : (isZh ? '黑方部队' : 'BLACK ARMY');
        
        let desc = '';
        if (isZh) {
            if (card.isFlag) desc = '军旗：不可移动、无防御力。敌方任何兵种进驻即获胜！';
            else if (card.isBomb) desc = '炸弹：正交行军1格。与任何敌方单位接触同归于尽；踩中军旗则获胜！';
            else if (card.isLandmine) desc = '地雷：严禁移动。非工兵进攻必被炸死；仅工兵可安全拆除并缴获地雷。';
            else if (card.isSapper || card.isMochigoma) desc = '工兵：唯一能拆除并俘获地雷的兵种。在普通作战中不敌2-10级军官。';
            else desc = `军官：根据军阶点数大吃小 10 > 9 > ... > 2，同级拼杀同归于尽。`;
        } else {
            if (card.isFlag) desc = 'Flag: Immobile and defenseless. Any piece capturing it wins immediately!';
            else if (card.isBomb) desc = 'Bomb: Mobile 1 step. Mutual elimination with any piece; captures Flag to win!';
            else if (card.isLandmine) desc = 'Landmine: Immobile perimeter defense. Destroys any non-Sapper that attacks it.';
            else if (card.isSapper || card.isMochigoma) desc = 'Sapper: Pioneer engineer. The only unit that can disarm and capture Landmines.';
            else desc = `Officer: Combat resolved by numeric hierarchy 10 > 9 > ... > 2. Ties destroy both.`;
        }

        inspectCardInfoEl.innerHTML = `
            <div style="font-size:1.05rem; font-weight:800; color:var(--gold); margin-bottom:4px;">${card.isFlag ? '★' : card.rank} · ${card.roleName}</div>
            <div style="color:#aaa; font-size:0.75rem; margin-bottom:6px; letter-spacing:0.5px;">${ownerName} • ${card.isImmobile ? (isZh ? '不可移动' : 'IMMOBILE') : (isZh ? '可移动' : 'MOBILE')}</div>
            <div style="color:#e0eae4; font-size:0.82rem; line-height:1.5;">${desc}</div>
        `;
        cardInspectModalEl.style.display = 'flex';
    }

    window.renderApp = render;
    updateAllLocalizedText();
    showHomepage();

    // =========================================================================
    // ONLINE MULTIPLAYER CONTROLLER (PHASE 4)
    // =========================================================================

    const tabPvpLocalBtn = document.getElementById('tabPvpLocalBtn');
    const tabPvpOnlineBtn = document.getElementById('tabPvpOnlineBtn');
    const pvpLocalContent = document.getElementById('pvpLocalContent');
    const pvpOnlineContent = document.getElementById('pvpOnlineContent');
    const onlineNicknameInput = document.getElementById('onlineNicknameInput');
    const createOnlineRoomBtn = document.getElementById('createOnlineRoomBtn');
    const refreshRoomsBtn = document.getElementById('refreshRoomsBtn');
    const onlineRoomListContainer = document.getElementById('onlineRoomListContainer');
    const onlineNotice = document.getElementById('onlineNotice');

    const onlineStatusBarEl = document.getElementById('onlineStatusBar');
    const onlineMatchLabel = document.getElementById('onlineMatchLabel');
    const onlineTurnBanner = document.getElementById('onlineTurnBanner');
    const onlineTimerPill = document.getElementById('onlineTimerPill');
    const onlineDisconnectNotice = document.getElementById('onlineDisconnectNotice');
    const onlineDisconnectMsg = document.getElementById('onlineDisconnectMsg');

    const forfeitModal = document.getElementById('forfeitModal');
    const confirmForfeitBtn = document.getElementById('confirmForfeitBtn');
    const cancelForfeitBtn = document.getElementById('cancelForfeitBtn');

    let onlineTimerInterval = null;
    let onlineTimerSeconds = 60;

    function confirmForfeitThen(actionCallback) {
        if (window.networkClient && window.networkClient.isOnlineMatch && game.gameState === 'playing') {
            if (forfeitModal) {
                forfeitModal.style.display = 'flex';
                const onConfirm = () => {
                    forfeitModal.style.display = 'none';
                    confirmForfeitBtn.removeEventListener('click', onConfirm);
                    cancelForfeitBtn.removeEventListener('click', onCancel);
                    window.networkClient.sendForfeit();
                    window.networkClient.resetMatch();
                    actionCallback();
                };
                const onCancel = () => {
                    forfeitModal.style.display = 'none';
                    confirmForfeitBtn.removeEventListener('click', onConfirm);
                    cancelForfeitBtn.removeEventListener('click', onCancel);
                };
                confirmForfeitBtn.addEventListener('click', onConfirm);
                cancelForfeitBtn.addEventListener('click', onCancel);
                return;
            }
        }
        actionCallback();
    }

    // Intercept homeBtn
    if (homeBtn) {
        homeBtn.onclick = (e) => {
            e.preventDefault();
            confirmForfeitThen(showHomepage);
        };
    }

    // Intercept newGameBtn
    if (newGameBtn) {
        newGameBtn.onclick = (e) => {
            e.preventDefault();
            confirmForfeitThen(() => {
                if (game.playerCount === 4) {
                    start4PGame(game.fourPlayerMode, game.pvpAlliance, game.playerSeat);
                } else if (game.mode === 'pve') {
                    startPvEGame(game.aiLevel, game.humanSide);
                } else {
                    startPvP1v1Game('red');
                }
            });
        };
    }

    // PvP sub-tab switching
    if (tabPvpLocalBtn && tabPvpOnlineBtn) {
        tabPvpLocalBtn.addEventListener('click', () => {
            tabPvpLocalBtn.classList.add('active');
            tabPvpOnlineBtn.classList.remove('active');
            if (pvpLocalContent) pvpLocalContent.style.display = 'block';
            if (pvpOnlineContent) pvpOnlineContent.style.display = 'none';
        });

        tabPvpOnlineBtn.addEventListener('click', () => {
            tabPvpOnlineBtn.classList.add('active');
            tabPvpLocalBtn.classList.remove('active');
            if (pvpLocalContent) pvpLocalContent.style.display = 'none';
            if (pvpOnlineContent) pvpOnlineContent.style.display = 'block';
            loadOnlineLobby();
        });
    }

    function loadOnlineLobby() {
        if (!window.networkClient) return;
        if (onlineNotice) onlineNotice.textContent = '';
        window.networkClient.connectLobby();

        window.networkClient.fetchPublicRooms().then(rooms => {
            if (rooms === null) {
                if (onlineNotice) {
                    onlineNotice.textContent = window.I18N ? window.I18N.t('server_offline_msg') : 'Cannot connect to online server.';
                    onlineNotice.style.color = '#ff9800';
                }
            } else {
                renderLobbyRooms(rooms);
            }
        });
    }

    function renderLobbyRooms(rooms) {
        if (!onlineRoomListContainer) return;
        onlineRoomListContainer.innerHTML = '';

        if (!rooms || rooms.length === 0) {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'room-list-empty';
            emptyDiv.style.textAlign = 'center';
            emptyDiv.style.padding = '18px 10px';
            emptyDiv.style.color = '#888';
            emptyDiv.style.fontSize = '0.82rem';
            emptyDiv.textContent = window.I18N ? window.I18N.t('no_rooms_found') : 'No waiting rooms available. Create one to begin!';
            onlineRoomListContainer.appendChild(emptyDiv);
            return;
        }

        rooms.forEach(room => {
            const item = document.createElement('div');
            item.className = 'room-item';

            const info = document.createElement('div');
            info.className = 'room-item-info';

            const hostSpan = document.createElement('strong');
            hostSpan.textContent = room.hostNickname || 'Host';

            const sideBadge = document.createElement('span');
            sideBadge.style.fontSize = '0.72rem';
            sideBadge.style.padding = '1px 6px';
            sideBadge.style.borderRadius = '3px';
            sideBadge.style.background = room.sidePreference === 'red' ? '#b22222' : (room.sidePreference === 'black' ? '#222' : '#555');
            sideBadge.style.color = '#fff';
            sideBadge.textContent = room.sidePreference.toUpperCase();

            info.appendChild(hostSpan);
            info.appendChild(sideBadge);

            const joinBtn = document.createElement('button');
            joinBtn.className = 'room-join-btn';
            joinBtn.textContent = window.I18N ? window.I18N.t('btn_join') : 'Join';
            joinBtn.addEventListener('click', () => {
                const nick = (onlineNicknameInput && onlineNicknameInput.value.trim()) || 'Player';
                window.networkClient.joinRoom(room.roomId, nick);
                if (onlineNotice) onlineNotice.textContent = window.I18N ? window.I18N.t('waiting_for_opponent') : 'Connecting...';
            });

            item.appendChild(info);
            item.appendChild(joinBtn);
            onlineRoomListContainer.appendChild(item);
        });
    }

    if (refreshRoomsBtn) {
        refreshRoomsBtn.addEventListener('click', () => {
            loadOnlineLobby();
        });
    }

    if (createOnlineRoomBtn) {
        createOnlineRoomBtn.addEventListener('click', () => {
            const nick = (onlineNicknameInput && onlineNicknameInput.value.trim()) || 'General';
            const sidePref = document.querySelector('input[name="onlineSidePref"]:checked')?.value || 'random';
            window.networkClient.createRoom(nick, sidePref);
            if (onlineNotice) {
                const hint = window.I18N ? window.I18N.t('room_created_hint') : 'Waiting for an opponent to join...';
                const cancelText = window.I18N ? window.I18N.t('cancel_waiting_btn') : 'Cancel';
                const copyText = window.I18N ? window.I18N.t('copy_room_link_btn') : 'Copy Link';
                onlineNotice.innerHTML = `
                    <div class="online-waiting-card">
                        <div><span class="waiting-spinner"></span>${hint}</div>
                        <div class="waiting-actions">
                            <button id="cancelWaitingBtn" class="btn-secondary">${cancelText}</button>
                            <button id="copyRoomLinkBtn" class="btn-secondary">${copyText}</button>
                        </div>
                    </div>
                `;
                const cancelBtn = document.getElementById('cancelWaitingBtn');
                if (cancelBtn) {
                    cancelBtn.addEventListener('click', () => {
                        window.networkClient.resetMatch();
                        loadOnlineLobby();
                    });
                }
                const copyBtn = document.getElementById('copyRoomLinkBtn');
                if (copyBtn) {
                    copyBtn.addEventListener('click', () => {
                        const url = window.location.origin + window.location.pathname;
                        navigator.clipboard.writeText(url).then(() => {
                            showToast(window.I18N ? window.I18N.t('room_link_copied') : 'Link copied!');
                        }).catch(() => {
                            showToast(url);
                        });
                    });
                }
            }
        });
    }

    function updateOnlineTimer(remainingMs) {
        clearInterval(onlineTimerInterval);
        if (!onlineTimerPill) return;

        onlineTimerSeconds = Math.max(0, Math.ceil(remainingMs / 1000));
        onlineTimerPill.textContent = `⏱ ${onlineTimerSeconds}s`;

        if (onlineTurnBanner) {
            const isMyTurn = (window.networkClient && game.currentTurn === window.networkClient.playerColor);
            onlineTurnBanner.textContent = isMyTurn ? 
                (window.I18N ? window.I18N.t('your_turn_banner') : 'YOUR TURN') : 
                (window.I18N ? window.I18N.t('opponent_turn_banner') : "OPPONENT'S TURN");
            onlineTurnBanner.style.color = isMyTurn ? 'var(--gold)' : '#aaa';
            onlineTurnBanner.style.borderColor = isMyTurn ? 'rgba(212,175,55,0.5)' : 'rgba(255,255,255,0.2)';
        }

        onlineTimerInterval = setInterval(() => {
            if (onlineTimerSeconds > 0) {
                onlineTimerSeconds--;
                onlineTimerPill.textContent = `⏱ ${onlineTimerSeconds}s`;
                const isMyTurn = (window.networkClient && game.currentTurn === window.networkClient.playerColor);
                if (onlineTimerSeconds <= 10 && isMyTurn && window.soundFX && typeof window.soundFX.playTimerTick === 'function') {
                    window.soundFX.playTimerTick();
                }
            } else {
                clearInterval(onlineTimerInterval);
            }
        }, 1000);
    }

    function stopOnlineTimer() {
        clearInterval(onlineTimerInterval);
    }

    function deserializeCard(p, fallbackOwner = 'red') {
        if (!p) return null;
        if (p instanceof Card) return p;
        const player = p.player || fallbackOwner;
        const isJoker = !!p.isFlag || p.rank === 'JOKER';
        const card = new Card(player, p.suit, p.rank, isJoker);
        card.originalOwner = p.originalOwner || player;
        card.team = p.team || player;
        card.faceUp = !!p.faceUp;
        card.isFlag = !!p.isFlag || isJoker;
        card.isBomb = !!p.isBomb || p.rank === 'K';
        card.isLandmine = !!p.isLandmine || p.rank === 'Q' || p.rank === 'J';
        card.isSapper = !!p.isSapper || p.rank === 'A' || !!p.isMochigoma;
        card.isMochigoma = !!p.isMochigoma;
        return card;
    }

    function applyServerStateView(payload) {
        if (!payload) return;

        const wasMyTurn = (game.currentTurn === payload.yourSide && game.gameState === 'playing');
        const isMyTurnNow = (payload.currentTurn === payload.yourSide && payload.gameState === 'playing');
        if (!wasMyTurn && isMyTurnNow && window.soundFX && typeof window.soundFX.playTurnNotification === 'function') {
            window.soundFX.playTurnNotification();
        }

        game.gameState = payload.gameState;
        game.currentTurn = payload.currentTurn;
        game.humanSide = payload.yourSide;
        game.mode = 'online';

        // Populate board
        for (let r = 0; r < 12; r++) {
            for (let c = 0; c < 5; c++) {
                const p = payload.board[r][c];
                if (!p) {
                    game.board[r][c] = null;
                } else {
                    game.board[r][c] = deserializeCard(p, p.player);
                }
            }
        }

        // Populate hands
        for (const color of ['red', 'black']) {
            const h = payload.hands[color];
            if (h) {
                game.hands[color].startingReserves = (h.startingReserves || []).map(p => deserializeCard(p, color));
                if (color !== payload.yourSide && h.startingReserveCount) {
                    while (game.hands[color].startingReserves.length < h.startingReserveCount) {
                        const fake = new Card(color, null, null, false);
                        fake.faceUp = false;
                        game.hands[color].startingReserves.push(fake);
                    }
                }

                game.hands[color].mochigoma = (h.mochigoma || []).map(p => {
                    const c = deserializeCard(p, color);
                    c.isMochigoma = true;
                    c.faceUp = true;
                    return c;
                });
            }
        }

        // Populate graveyard
        game.graveyard = (payload.graveyard || []).map(p => deserializeCard(p, p.originalOwner));

        // Hide setup toolbar, show status bar
        if (setupToolbarEl) setupToolbarEl.style.display = 'none';
        if (statusBarEl) statusBarEl.style.display = 'flex';
        if (onlineStatusBarEl) onlineStatusBarEl.style.display = 'flex';
        if (onlineDisconnectNotice) onlineDisconnectNotice.style.display = 'none';

        if (onlineMatchLabel) {
            const oppName = window.networkClient?.opponentNickname || 'Opponent';
            onlineMatchLabel.textContent = `Online: ${payload.yourSide.toUpperCase()} vs ${oppName}`;
        }

        updateOnlineTimer(payload.turnTimerRemainingMs);
        render();
    }

    // Wire Network Client Events
    if (window.networkClient) {
        window.networkClient.on('lobbyUpdate', (rooms) => {
            renderLobbyRooms(rooms);
        });

        window.networkClient.on('setupStart', (payload) => {
            showGame();
            if (window.soundFX && typeof window.soundFX.playJoinNotification === 'function') {
                window.soundFX.playJoinNotification();
            }
            if (onlineNotice) onlineNotice.textContent = '';
            game.resetForNewGame({ mode: 'online', humanSide: payload.playerColor });
            game.setupPlayer = payload.playerColor;
            game.gameState = 'setup';

            if (setupToolbarEl) setupToolbarEl.style.display = 'flex';
            if (statusBarEl) statusBarEl.style.display = 'none';
            if (onlineStatusBarEl) onlineStatusBarEl.style.display = 'none';

            if (setupConfirmBtn) {
                setupConfirmBtn.disabled = false;
                setupConfirmBtn.textContent = window.I18N ? window.I18N.t('confirm_battle') : 'Confirm & Battle';
                setupConfirmBtn.classList.add('btn-pulse');
            }

            showToast(window.I18N ? window.I18N.t('opponent_joined') : 'Opponent joined! Deploy your formation.');
            render();
        });

        window.networkClient.on('stateView', (payload) => {
            applyServerStateView(payload);
        });

        window.networkClient.on('actionResult', (payload) => {
            if (payload.clash) {
                activeClash = payload.clash;
                activeClash.attacker = deserializeCard(payload.clash.attacker, 'red');
                activeClash.defender = deserializeCard(payload.clash.defender, 'black');
                game.lastClashResult = activeClash;
                showClashModal(activeClash);

                // Sound FX Parity with PvE
                const s = payload.clash.sound;
                if (s === 'bomb') {
                    window.soundFX.playBomb();
                } else if (s === 'defuse') {
                    window.soundFX.playDefuse();
                } else if (s === 'victory') {
                    window.soundFX.playVictory();
                } else {
                    window.soundFX.playClash();
                }

                // Log combat verdict to battlefield log
                const verdict = getLocalizedClashVerdict(activeClash) || payload.clash.outcomeText;
                if (verdict) game.log(verdict);
            } else {
                window.soundFX.playMove();
                if (payload.action?.to) {
                    const toPos = `(${String.fromCharCode(65 + payload.action.to.c)}${payload.action.to.r + 1})`;
                    const p = payload.action.player ? payload.action.player.toUpperCase() : 'Unit';
                    const isZh = window.I18N && window.I18N.currentLang === 'zh';
                    const pName = isZh ? (payload.action.player === 'red' ? '红方' : '黑方') : p;
                    const msg = window.I18N ? window.I18N.t('advance_move', { player: pName, pos: toPos }) : `${p} advanced to ${toPos}.`;
                    game.log(msg);
                }
            }
        });

        window.networkClient.on('opponentStatus', (payload) => {
            if (!onlineDisconnectNotice) return;
            if (!payload.connected) {
                onlineDisconnectNotice.style.display = 'block';
                const sec = Math.ceil((payload.gracePeriodRemainingMs || 60000) / 1000);
                if (onlineDisconnectMsg) {
                    onlineDisconnectMsg.textContent = window.I18N ? 
                        window.I18N.t('opponent_disconnected_alert', { sec }) : 
                        `Opponent disconnected! Reconnect grace: ${sec}s`;
                }
            } else {
                onlineDisconnectNotice.style.display = 'none';
            }
        });

        window.networkClient.on('gameOver', (payload) => {
            game.gameState = 'gameover';
            game.winner = payload.winner;
            game.winReason = payload.reason;
            stopOnlineTimer();
            if (clashModalEl.style.display !== 'flex') {
                setTimeout(() => {
                    showGameOver(payload.reason);
                }, 100);
            }
        });

        window.networkClient.on('setupConfirmed', (payload) => {
            clearTimeout(window.__setupConfirmWatchdog);
            if (setupConfirmBtn) {
                setupConfirmBtn.disabled = true;
                setupConfirmBtn.textContent = window.I18N ? window.I18N.t('waiting_for_opponent') : 'Waiting...';
            }
        });

        window.networkClient.on('error', (payload) => {
            clearTimeout(window.__setupConfirmWatchdog);
            if (payload.pleaseRefresh) {
                alert(window.I18N ? window.I18N.t('refresh_required') : 'A newer version is available. Please refresh.');
            } else {
                const msg = payload.errors ? payload.errors.join('\n') : (payload.message || payload.code || 'An error occurred.');
                showToast(msg);
                if (game.gameState === 'setup' && setupConfirmBtn) {
                    setupConfirmBtn.disabled = false;
                    setupConfirmBtn.textContent = window.I18N ? window.I18N.t('confirm_battle') : 'Confirm & Battle';
                }
            }
        });

        window.networkClient.on('connectionChange', (status) => {
            if (status === 'offline' && onlineNotice) {
                onlineNotice.textContent = window.I18N ? window.I18N.t('server_offline_msg') : 'Cannot connect to online server.';
                onlineNotice.style.color = '#ff9800';
            }
        });
    }

});
