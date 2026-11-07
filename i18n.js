// Internationalization (i18n) Engine for Poker Chess

function safeGetStorage(key, fallback) {
    try {
        if (typeof localStorage !== 'undefined') {
            const val = localStorage.getItem(key);
            return val !== null ? val : fallback;
        }
    } catch (e) {
        // Storage restricted or private browsing mode
    }
    return fallback;
}

function safeSetStorage(key, val) {
    try {
        if (typeof localStorage !== 'undefined') {
            localStorage.setItem(key, val);
        }
    } catch (e) {
        // Storage restricted or private browsing mode
    }
}

const I18N = {
    currentLang: safeGetStorage('psj_lang', 'en'),
    currentTheme: safeGetStorage('psj_theme', 'felt'),
    currentCardStyle: safeGetStorage('psj_card_style', 'art'),

    dict: {
        en: {
            title: "POKER CHESS",
            subtitle: "",
            mode_pve: "PvE",
            mode_pvp: "PvP",
            mode_4p_2v2: "2v2",
            mode_4p_ffa: "1v1v1v1",
            mode_sandbox: "Sandbox",
            seating_opposite: "A/C vs B/D",
            seating_adj_nw_se: "A/B vs C/D",
            seating_adj_ne_sw: "A/D vs B/C",
            home: "Homepage",
            new_game: "New Game",
            settings: "Settings",
            
            // Turn indicator
            turn_red: "Red's Turn",
            turn_black: "Black's Turn",
            turn_gen_a: "A's Turn",
            turn_gen_b: "B's Turn",
            turn_gen_c: "C's Turn",
            turn_gen_d: "D's Turn",
            gen_a: "A",
            gen_b: "B",
            gen_c: "C",
            gen_d: "D",
            auto_fill_all: "Auto-Fill All",
            start_battle_4p: "Start 4-Player Battle",
            player_eliminated: "{player} Flag captured! Army eliminated.",
            team_red_wins: "Red Team Wins",
            team_black_wins: "Black Team Wins",
            player_wins: "{player} Wins",
            setup_turn_red: "RED DEPLOYMENT",
            setup_turn_black: "BLACK DEPLOYMENT",

            // Army counts
            red_army: "Red:",
            black_army: "Black:",
            native: "Native",
            mochigoma: "Conscripts",
            cap: "Cap",

            // Deployment Toolbar
            deployment_phase: "DEPLOYMENT PHASE:",
            camp: "Camp:",
            reserves: "Reserves:",
            unplaced: "Unplaced:",
            formation_ready: "Formation ready!",
            auto_fill: "Auto-Fill Preset",
            clear_formation: "Clear Formation",
            to_reserve: "To Reserve",
            confirm_battle: "Confirm & Battle",
            unplaced_cards: "Unplaced Cards",
            click_to_place: "",
            empty_reserve: "Empty Reserve",

            // Sidebars
            p2_starting_reserve: "Black Reserve",
            p2_mochigoma: "Black Conscripts",
            p1_starting_reserve: "Red Reserve",
            p1_mochigoma: "Red Conscripts",
            secret_drops: "",
            face_up_sappers: "",
            graveyard: "Graveyard",
            battlefield_log: "Battlefield Log",

            // Card Roles (Zero Tautology: No numbers in role names!)
            role_flag: "Flag",
            role_bomb: "Bomb",
            role_landmine: "Landmine",
            role_sapper: "Sapper",
            role_officer: "Officer",
            role_conscript: "Sapper",
            badge_conscript: "SAPPER",

            // Clash Modal
            clash_title: "COMBAT CLASH REVEAL",
            clash_attacker: "ATTACKER",
            clash_defender: "DEFENDER",
            clash_continue: "Continue Battle",

            // Combat & Event Messages
            win_red: "Red Wins",
            win_black: "Black Wins",
            draw: "Draw",
            assassination: "{player} Wins",
            bomb_explosion: "BOMB EXPLOSION! Both units were annihilated!",
            mine_cleared: "MINE CLEARED! Sapper disarmed and captured Landmine!",
            mine_detonation: "DETONATION! Attacking {attacker} destroyed by Landmine!",
            sapper_clash: "Sapper Clash! Mutual destruction.",
            conscript_clash: "Conscript Clash! Both traitors sent to Graveyard.",
            sapper_executed_conscript: "{player} Sapper executed enemy Conscript!",
            officer_captured_sapper: "{player} Officer captured attacking Sapper!",
            sapper_captured_by_officer: "{player} Officer captured defending Sapper!",
            officer_executed_conscript: "{player} Officer executed enemy Conscript!",
            conscript_executed: "Traitor Conscript executed! Sent to Graveyard.",
            officer_victory: "VICTORY! {player} defeated opponent Officer!",
            officer_defeat: "DEFEAT! {player} Officer defeated attacking unit!",
            officer_tie: "TIED RANKS! Both officers destroyed in mutual combat!",
            mutiny_excess: "ANTI-MUTINY RULE: Conscription limit reached! Prisoner sent to Graveyard.",
            mutiny_enforced_hand: "ANTI-MUTINY: Conscripts exceeded loyal troops! 1 prisoner in hand discarded to Graveyard.",
            mutiny_enforced_board: "ANTI-MUTINY: Conscript Sapper disbanded to Graveyard!",
            drop_secret: "{player} dropped a Secret Reserve.",
            drop_conscript: "{player} dropped a Conscript Sapper.",
            advance_move: "{player} advanced to {pos}.",
            repetition_draw: "DRAW: Threefold repetition of the board position!",
            no_moves: "{winner} WINS: {loser} has no remaining legal moves!",

            // Settings Modal
            settings_title: "Game Settings",
            language_heading: "Language",
            card_style_heading: "Card Style",
            style_simplified: "Simplified",
            style_art: "Art Mode",
            sound_heading: "Sound Effects",
            sound_desc: "Web Audio sfx",
            sound_enabled: "Sound Enabled",
            sound_muted: "Muted",
            theme_heading: "Board Appearance",
            theme_felt: "Classic Felt",
            theme_wood: "Mahogany Wood",
            theme_obsidian: "Obsidian Midnight",
            rulebook_heading: "Rulebook",
            rulebook_open: "Open Rulebook",
            close_btn: "Done",
            inspect_title: "Card Details",
            inspect_hint: "Click any card in Graveyard or Hand to inspect full art",
            table_frontline_banner: "NEUTRAL FRONTLINE BUFFER ZONE",

            // Homepage
            home_modes: "Homepage",
            homepage_title: "POKER CHESS",
            homepage_subtitle: "",
            tab_pve: "PvE",
            tab_pvp: "PvP",
            ai_difficulty_title: "CPU Level",
            ai_level_low: "Low",
            ai_level_medium: "Medium",
            ai_level_high: "High",
            side_select_title: "Side",
            side_red: "Red",
            side_black: "Black",
            pvp_format_title: "Mode",
            pvp_1v1: "1v1",
            pvp_2v2: "2v2",
            pvp_ffa: "1v1v1v1",
            pvp_side_title_1v1: "Side",
            pvp_alliance_title_2v2: "Side",
            alliance_clubs: "Clubs",
            alliance_hearts: "Hearts",
            pvp_seating_title_2v2: "Seating",
            seat_select_title_ffa: "Seat",
            seat_a: "A",
            seat_b: "B",
            seat_c: "C",
            seat_d: "D",
            launch_pve_btn: "Start Game",
            launch_pvp_btn: "Start Game",
            cancel_btn: "Cancel",
            rulebook_btn: "Rulebook",

            // Alerts & Errors
            invalid_frontline: "Flag and Landmines CANNOT be placed on the frontline!",
            setup_incomplete_camp: "Camp must have exactly 25 cards placed ({count}/25).",
            setup_incomplete_reserve: "Must have exactly 2 Reserves in hand ({count}/2).",
            max_reserves_reached: "Reserves already has the maximum of 2 cards!",
            select_card_first: "Please first select a card on the board or in the Unplaced tray to move to Reserves.",
            immobile_alert: "{role} is strictly immobile! It cannot move or initiate attacks.",
            unit_blocked: "Unit is blocked by friendly troops in front. Advance your frontline first!",
            formation_ready_prompt: "Formation deployed! Tap 'Confirm & Battle' to begin marching.",
            turn_1_hint: "Turn 1: Select a frontline unit to march forward!",
            drop_camp_only: "You can only place cards in your 5×5 home camp!",
            // Online PvP
            pvp_local_title: "Local (Same Device)",
            pvp_online_title: "Online Matchmaking",
            online_nickname: "Your Nickname",
            create_room_btn: "+ Create Room",
            refresh_rooms_btn: "Refresh",
            public_rooms_title: "Available Public Rooms",
            no_rooms_found: "No waiting rooms available. Create one to begin!",
            room_host: "Host",
            room_side: "Side",
            side_random: "Random",
            btn_join: "Join",
            waiting_for_opponent: "Waiting for an opponent to join...",
            opponent_joined: "Opponent joined! Deploy your formation.",
            online_status_bar: "Online: {you} vs {opponent}",
            turn_timer_label: "Time Left",
            your_turn_banner: "YOUR TURN",
            opponent_turn_banner: "OPPONENT'S TURN",
            opponent_disconnected_alert: "Opponent disconnected! Reconnect grace: {sec}s",
            server_offline_msg: "Cannot connect to online server. Local PvE is still available.",
            forfeit_confirm_title: "Forfeit Match?",
            forfeit_confirm_body: "Leaving this online match will forfeit the game to your opponent. Are you sure?",
            forfeit_confirm_btn: "Forfeit & Leave",
            forfeit_cancel_btn: "Stay in Match",
            reconnecting_banner: "Reconnecting to server...",
            cancel_waiting_btn: "Cancel Waiting",
            copy_room_link_btn: "Copy Link",
            room_link_copied: "Room link copied to clipboard!",
            room_created_hint: "Room created! Waiting for a challenger to join...",
            timer_warning_hint: "Time is running out!",
        },

        zh: {
            title: "扑克棋",
            subtitle: "",
            mode_pve: "PvE",
            mode_pvp: "PvP",
            mode_4p_2v2: "2v2",
            mode_4p_ffa: "1v1v1v1",
            mode_sandbox: "沙盒",
            seating_opposite: "A/C 对 B/D",
            seating_adj_nw_se: "A/B 对 C/D",
            seating_adj_ne_sw: "A/D 对 B/C",
            home: "首页",
            new_game: "新局",
            settings: "设置",

            // Turn indicator
            turn_red: "红方回合",
            turn_black: "黑方回合",
            turn_gen_a: "A 回合",
            turn_gen_b: "B 回合",
            turn_gen_c: "C 回合",
            turn_gen_d: "D 回合",
            gen_a: "A",
            gen_b: "B",
            gen_c: "C",
            gen_d: "D",
            auto_fill_all: "一键部署四方大营",
            start_battle_4p: "开战",
            player_eliminated: "{player} 军旗被夺，全军阵亡溃散！",
            team_red_wins: "红方联军获胜",
            team_black_wins: "黑方联军获胜",
            player_wins: "{player} 胜出",
            setup_turn_red: "红方布阵",
            setup_turn_black: "黑方布阵",

            // Army counts
            red_army: "红方:",
            black_army: "黑方:",
            native: "主力",
            mochigoma: "战俘",
            cap: "上限",

            // Deployment Toolbar
            deployment_phase: "布阵阶段:",
            camp: "本营:",
            reserves: "预备队:",
            unplaced: "未布设:",
            formation_ready: "阵型合法，可以开战！",
            auto_fill: "一键推荐布阵",
            clear_formation: "全部撤回重置",
            to_reserve: "设为预备队",
            confirm_battle: "确认布阵 · 开战！",
            unplaced_cards: "待布阵棋子",
            click_to_place: "",
            empty_reserve: "暂无预备兵力",

            // Sidebars
            p2_starting_reserve: "黑方预备队",
            p2_mochigoma: "黑方战俘营",
            p1_starting_reserve: "红方预备队",
            p1_mochigoma: "红方战俘营",
            secret_drops: "",
            face_up_sappers: "",
            graveyard: "阵亡墓地",
            battlefield_log: "战报记录",

            // Card Roles (No Tautology!)
            role_flag: "军旗",
            role_bomb: "炸弹",
            role_landmine: "地雷",
            role_sapper: "工兵",
            role_officer: "军官",
            role_conscript: "工兵",
            badge_conscript: "工兵",

            // Clash Modal
            clash_title: "战斗揭牌结算",
            clash_attacker: "进攻方",
            clash_defender: "防守方",
            clash_continue: "继续战斗",

            // Combat & Event Messages
            win_red: "红方胜",
            win_black: "黑方胜",
            draw: "和棋",
            assassination: "{player}胜",
            bomb_explosion: "炸弹引爆！双方部队同归于尽，送入墓地！",
            mine_cleared: "排雷成功！工兵成功拆除并缴获地雷！",
            mine_detonation: "地雷爆炸！进攻方 {attacker} 被地雷消灭！",
            sapper_clash: "工兵交锋！双方同归于尽。",
            conscript_clash: "动员兵交锋！双方叛军同归于尽，送入墓地。",
            sapper_executed_conscript: "{player} 工兵击杀叛军动员兵！",
            officer_captured_sapper: "{player} 军官击溃并捕获敌方工兵！",
            sapper_captured_by_officer: "{player} 军官消灭敌方进攻工兵！",
            officer_executed_conscript: "{player} 军官处决敌方动员兵！",
            conscript_executed: "叛军动员兵被处决！送入阵亡墓地。",
            officer_victory: "战斗胜利！{player} 军官击败敌方部队！",
            officer_defeat: "进攻受挫！{player} 防守军官歼灭进攻部队！",
            officer_tie: "势均力敌！同级军官拼杀同归于尽！",
            mutiny_excess: "兵变法则触发：战俘数量已达本军上限，多余战俘处决送入墓地！",
            mutiny_enforced_hand: "兵变法则触发：主力受损致兵力失衡，手牌1张战俘移送墓地！",
            mutiny_enforced_board: "兵变法则触发：战俘工兵发生溃散，移出棋盘！",
            drop_secret: "{player} 暗置空降了1支秘密预备部队。",
            drop_conscript: "{player} 空降了1名明置战俘工兵。",
            advance_move: "{player} 行军进驻 {pos}。",
            repetition_draw: "和棋：棋局三次重复相同局面！",
            no_moves: "{winner} 获胜：{loser} 已无任何合法可行步骤！",

            // Settings Modal
            settings_title: "游戏设置",
            language_heading: "语言",
            card_style_heading: "卡牌风格",
            style_simplified: "极简模式",
            style_art: "艺术模式",
            sound_heading: "音效系统",
            sound_desc: "原生 Web Audio 合成音效",
            sound_enabled: "开启音效",
            sound_muted: "静音",
            theme_heading: "棋盘外观",
            theme_felt: "经典绒面",
            theme_wood: "典雅红木",
            theme_obsidian: "暗夜曜黑",
            rulebook_heading: "规则手册",
            rulebook_open: "查看指南",
            close_btn: "完成",
            inspect_title: "完整卡牌全貌",
            inspect_hint: "点击墓地或手牌中的卡牌可查看完整大图",
            table_frontline_banner: "中立前线停火缓冲区",

            // Homepage
            home_modes: "首页",
            homepage_title: "扑克棋",
            homepage_subtitle: "",
            tab_pve: "PvE",
            tab_pvp: "PvP",
            ai_difficulty_title: "人机难度",
            ai_level_low: "初级",
            ai_level_medium: "中级",
            ai_level_high: "高级",
            side_select_title: "阵营",
            side_red: "红方",
            side_black: "黑方",
            pvp_format_title: "模式",
            pvp_1v1: "1v1",
            pvp_2v2: "2v2",
            pvp_ffa: "1v1v1v1",
            pvp_side_title_1v1: "阵营",
            pvp_alliance_title_2v2: "阵营",
            alliance_clubs: "梅花盟",
            alliance_hearts: "红桃盟",
            pvp_seating_title_2v2: "布设",
            seat_select_title_ffa: "席位",
            seat_a: "A",
            seat_b: "B",
            seat_c: "C",
            seat_d: "D",
            launch_pve_btn: "开始游戏",
            launch_pvp_btn: "开始游戏",
            cancel_btn: "取消",
            rulebook_btn: "规则手册",

            // Alerts & Errors
            invalid_frontline: "军旗和地雷严禁布设在前沿第一排！",
            setup_incomplete_camp: "营地必须布设满25张牌 (当前: {count}/25)。",
            setup_incomplete_reserve: "初始预备队必须保留2张牌 (当前: {count}/2)。",
            max_reserves_reached: "初始预备队最多只能保留2张牌！",
            select_card_first: "请先在营地或待布阵栏选中一张牌，再点击放入预备队。",
            immobile_alert: "{role} 为不可移动单位，无法移动或主动进攻！",
            unit_blocked: "该部队被前方友军阻挡，请先移动前线部队！",
            formation_ready_prompt: "阵型已就绪！点击【确认开战】即可发起进攻！",
            turn_1_hint: "第1回合：选择前沿部队前进！",
            drop_camp_only: "只能将部队空降至本方5×5营地内的空位！",
            // Online PvP
            pvp_local_title: "本地同屏",
            pvp_online_title: "在线对战",
            online_nickname: "玩家昵称",
            create_room_btn: "+ 创建房间",
            refresh_rooms_btn: "刷新列表",
            public_rooms_title: "大厅等待中房间",
            no_rooms_found: "暂无在线房间，点击上方创建！",
            room_host: "房主",
            room_side: "阵营偏好",
            side_random: "随机",
            btn_join: "加入",
            waiting_for_opponent: "等待对手加入中...",
            opponent_joined: "对手已加入！请布设你的秘密防线。",
            online_status_bar: "在线对战：{you} vs {opponent}",
            turn_timer_label: "回合倒计时",
            your_turn_banner: "你的回合",
            opponent_turn_banner: "对手思考中",
            opponent_disconnected_alert: "对手已断线！重连倒计时：{sec}秒",
            server_offline_msg: "无法连接在线对战服务器，单机人机模式仍可正常游玩。",
            forfeit_confirm_title: "确认认输退出？",
            forfeit_confirm_body: "当前对局正在进行中，中途离开或重开将被判定为认输，是否确认？",
            forfeit_confirm_btn: "认输并退出",
            forfeit_cancel_btn: "继续对局",
            reconnecting_banner: "网络断开，正在尝试重连...",
            cancel_waiting_btn: "取消等待",
            copy_room_link_btn: "复制链接",
            room_link_copied: "房间链接已复制到剪贴板！",
            room_created_hint: "房间已创建！正在等待对手加入...",
            timer_warning_hint: "回合时间剩余不足10秒！",
        }
    },

    t(key, params = {}) {
        const langDict = this.dict[this.currentLang] || this.dict.en;
        let str = langDict[key] || this.dict.en[key] || key;
        for (const [k, v] of Object.entries(params)) {
            str = str.replace(`{${k}}`, v);
        }
        return str;
    },

    setLang(lang) {
        if (lang === 'en' || lang === 'zh') {
            this.currentLang = lang;
            safeSetStorage('psj_lang', lang);
            document.documentElement.lang = lang;
        }
    },

    setTheme(theme) {
        if (['felt', 'wood', 'obsidian'].includes(theme)) {
            this.currentTheme = theme;
            safeSetStorage('psj_theme', theme);
            document.body.setAttribute('data-theme', theme);
        }
    },

    setCardStyle(style) {
        if (style === 'simplified' || style === 'art') {
            this.currentCardStyle = style;
            safeSetStorage('psj_card_style', style);
            document.body.setAttribute('data-card-style', style);
        }
    },

    init() {
        this.setLang(this.currentLang);
        this.setTheme(this.currentTheme);
        this.setCardStyle(this.currentCardStyle);
    }
};

window.I18N = I18N;
