/* Duo Arcade - the shell around the games: rooms, invites, turns, rematches. */

(function () {
  const RENDERERS = window.GAMES || {};
  const $app = document.getElementById('app');
  const $toast = document.getElementById('toast');

  const S = {
    screen: 'home',
    catalog: [],
    room: null, player: null, token: null, name: null,
    view: null, lastV: 0,
    sheet: null,          // the "enter your name" panel
    rules: null,          // game key whose rules are on screen
    joinCode: '', joinInfo: null, joinError: '',
    homeError: '',
    ui: {}, uiKey: '',    // scratch space a game renderer keeps between redraws
  };

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const gameByKey = (key) => S.catalog.find((g) => g.key === key) || { name: 'Game', emoji: '🎮' };

  // ---------- remembering who you are ----------

  const store = {
    save() {
      localStorage.setItem('duoarcade', JSON.stringify({
        room: S.room, player: S.player, token: S.token, name: S.name,
      }));
    },
    load() {
      try { return JSON.parse(localStorage.getItem('duoarcade') || 'null'); } catch (e) { return null; }
    },
    clear() { localStorage.removeItem('duoarcade'); },
    name(value) {
      if (value !== undefined) localStorage.setItem('duoarcade.name', value);
      return localStorage.getItem('duoarcade.name') || '';
    },
  };

  // ---------- talking to the server ----------

  async function api(path, body) {
    const payload = Object.assign(
      { room: S.room, player: S.player, token: S.token }, body || {});
    try {
      const res = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({ error: 'Something went wrong.' }));
      return { ok: res.ok, status: res.status, data };
    } catch (err) {
      return { ok: false, status: 0, data: { error: "Can't reach the server — check your connection." } };
    }
  }

  let pollId = 0;

  async function startPolling() {
    const mine = ++pollId;
    while (mine === pollId && S.room) {
      let res;
      try {
        res = await fetch(`/api/state?room=${S.room}&player=${S.player}&v=${S.lastV}`);
      } catch (err) {
        await sleep(1500);
        continue;
      }
      if (mine !== pollId) return;
      if (res.status === 404) { endSession('That room has closed.'); return; }
      const data = await res.json().catch(() => null);
      if (data && data.v) applyView(data);
      else await sleep(1000);
    }
  }

  function applyView(data) {
    if (!data || !data.v) return;
    // The long poll gives up after a while and hands back an unchanged room.
    // Redrawing then would rebuild the whole screen for nothing - and a button
    // destroyed between finger-down and finger-up never fires its click, which
    // shows up as "I had to press it twice".
    const somethingChanged = data.v !== S.lastV || S.screen !== 'room';
    S.view = data;
    S.lastV = data.v;
    S.screen = 'room';
    const key = data.game + '#' + data.round;
    if (key !== S.uiKey) { S.uiKey = key; S.ui = {}; }  // fresh game, fresh scratch space
    if (somethingChanged) render();
  }

  function endSession(message) {
    pollId++;
    store.clear();
    Object.assign(S, { room: null, player: null, token: null, view: null, lastV: 0, screen: 'home', ui: {}, uiKey: '' });
    history.replaceState({}, '', '/');
    if (message) toast(message);
    render();
  }

  // ---------- little UI bits ----------

  let toastTimer = null;
  function toast(message) {
    $toast.textContent = message;
    $toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { $toast.hidden = true; }, 2600);
  }

  function inviteLink() {
    return `${location.origin}/?room=${S.room}`;
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast('Link copied!');
    } catch (err) {
      const box = document.createElement('textarea');
      box.value = text;
      document.body.append(box);
      box.select();
      try { document.execCommand('copy'); toast('Link copied!'); } catch (e) { toast('Copy this: ' + text); }
      box.remove();
    }
  }

  async function shareInvite() {
    const url = inviteLink();
    const game = gameByKey(S.view && S.view.game).name;
    if (navigator.share) {
      try {
        await navigator.share({ title: 'Duo Arcade', text: `Come play ${game} with me!`, url });
        return;
      } catch (err) { /* they closed the share sheet - fall through to copying */ }
    }
    copyText(url);
  }

  // ---------- home ----------

  function gameCard(game, onPick) {
    return h('button', { class: 'game-card', onclick: () => onPick(game) },
      h('div', { class: 'emoji' }, game.emoji),
      h('div', { class: 'name' }, game.name),
      h('div', { class: 'tag' }, game.tagline),
      h('div', { class: 'meta' },
        h('span', { class: 'pill ' + game.level }, game.level),
        h('span', { class: 'pill' }, game.minutes)));
  }

  function homeScreen() {
    return h('div', { class: 'wrap' },
      h('div', { class: 'hero' },
        h('div', { class: 'logo' }, '🎮'),
        h('h1', {}, 'Duo Arcade'),
        h('p', {}, 'Games for exactly two people. Pick one, send your friend the link, and play from your own phones.')),

      h('div', { class: 'section-title' },
        h('h2', {}, 'Choose a game'),
        h('span', { class: 'small muted' }, `${S.catalog.length} games`)),
      h('div', { class: 'grid-games' }, S.catalog.map((g) => gameCard(g, openCreateSheet))),

      h('div', { class: 'section-title' }, h('h2', {}, 'Got a room code?')),
      h('div', { class: 'panel' },
        h('label', { class: 'field' },
          h('span', {}, "Your friend's 4-letter code"),
          h('input', {
            class: 'code', id: 'joincode', maxlength: '4', autocapitalize: 'characters',
            autocomplete: 'off', placeholder: '••••',
            oninput: (e) => { e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ''); },
            onkeydown: (e) => { if (e.key === 'Enter') goToCode(); },
          })),
        h('button', { class: 'btn primary wide', onclick: goToCode }, 'Join the room'),
        S.homeError && h('div', { class: 'error' }, S.homeError)),

      S.sheet && createSheet());
  }

  async function goToCode() {
    const code = (document.getElementById('joincode').value || '').trim().toUpperCase();
    if (code.length !== 4) { S.homeError = 'A room code is 4 characters.'; render(); return; }
    S.homeError = '';
    S.joinCode = code;
    S.screen = 'join';
    S.joinInfo = null;
    S.joinError = '';
    render();
    peek(code);
  }

  function openCreateSheet(game) {
    S.sheet = { game, error: '' };
    render();
    const input = document.getElementById('sheetname');
    if (input) input.focus();
  }

  function createSheet() {
    const game = S.sheet.game;
    return h('div', {
      class: 'backdrop',
      onclick: (e) => { if (e.target.classList.contains('backdrop')) { S.sheet = null; render(); } },
    },
      h('div', { class: 'sheet' },
        h('div', { style: { fontSize: '2rem', lineHeight: '1' } }, game.emoji),
        h('h2', { style: { marginTop: '8px' } }, game.name),
        h('p', { class: 'rules' }, game.rules),
        h('label', { class: 'field' },
          h('span', {}, 'Your name'),
          h('input', {
            id: 'sheetname', maxlength: '16', placeholder: 'e.g. Sam', value: store.name(),
            autocomplete: 'given-name',
            onkeydown: (e) => { if (e.key === 'Enter') createRoom(); },
          })),
        h('div', { class: 'btn-row' },
          h('button', { class: 'btn ghost', onclick: () => { S.sheet = null; render(); } }, 'Back'),
          h('button', { class: 'btn primary', onclick: createRoom }, 'Create room')),
        S.sheet.error && h('div', { class: 'error' }, S.sheet.error)));
  }

  async function createRoom() {
    const name = (document.getElementById('sheetname').value || '').trim();
    if (!name) { S.sheet.error = 'Please enter your name.'; render(); return; }
    store.name(name);
    const res = await api('/api/create', { name, game: S.sheet.game.key });
    if (!res.ok) { S.sheet.error = res.data.error || 'Could not create the room.'; render(); return; }
    Object.assign(S, { room: res.data.room, player: 0, token: res.data.token, name, sheet: null, lastV: 0 });
    store.save();
    startPolling();
  }

  // ---------- joining ----------

  async function peek(code) {
    const res = await api('/api/peek', { room: code });
    if (!res.ok) { S.joinError = res.data.error || 'That room was not found.'; }
    else if (res.data.full) { S.joinError = 'That room already has two players.'; }
    else { S.joinInfo = res.data; }
    render();
  }

  function joinScreen() {
    const info = S.joinInfo;
    const game = info ? gameByKey(info.game) : null;
    return h('div', { class: 'wrap' },
      h('div', { class: 'hero' },
        h('div', { class: 'logo' }, game ? game.emoji : '🎮'),
        h('h1', {}, game ? game.name : 'Joining…'),
        info && h('p', {}, `${info.host} is waiting for you in room ${info.room}.`)),
      h('div', { class: 'panel' },
        S.joinError
          ? h('div', {},
            h('div', { class: 'error', style: { marginTop: '0' } }, S.joinError),
            h('button', {
              class: 'btn wide', style: { marginTop: '14px' },
              onclick: () => { S.screen = 'home'; S.joinError = ''; history.replaceState({}, '', '/'); render(); },
            }, 'Back to the arcade'))
          : !info
            ? h('div', { class: 'center muted' }, 'Looking for that room…')
            : h('div', {},
              h('p', { class: 'rules muted small', style: { marginTop: '0' } }, game.rules),
              h('label', { class: 'field' },
                h('span', {}, 'Your name'),
                h('input', {
                  id: 'joinname', maxlength: '16', placeholder: 'e.g. Alex', value: store.name(),
                  onkeydown: (e) => { if (e.key === 'Enter') joinRoom(); },
                })),
              h('button', { class: 'btn primary wide', onclick: joinRoom }, `Join ${info.host}`))));
  }

  async function joinRoom() {
    const name = (document.getElementById('joinname').value || '').trim();
    if (!name) { S.joinError = 'Please enter your name.'; render(); return; }
    store.name(name);
    const res = await api('/api/join', { room: S.joinInfo.room, name });
    if (!res.ok) { S.joinError = res.data.error || 'Could not join.'; render(); return; }
    Object.assign(S, { room: res.data.room, player: res.data.player, token: res.data.token, name, lastV: 0 });
    store.save();
    history.replaceState({}, '', '/');
    startPolling();
  }

  // ---------- the room ----------

  function topbar() {
    return h('div', { class: 'topbar' },
      h('button', { class: 'btn small ghost', onclick: leaveRoom }, '← Leave'),
      h('div', { class: 'code' }, S.view.code),
      h('button', { class: 'btn small', onclick: shareInvite }, '🔗 Invite'));
  }

  function scorebar() {
    const v = S.view;
    const turn = v.state ? v.state.turn : null;
    return h('div', { class: 'scorebar' }, [0, 1].map((p) => {
      const name = v.names[p];
      return h('div', { class: AR.join(['who', 'p' + p, turn === p && 'active']) },
        h('div', { class: 'nm' },
          h('span', { class: 'dot p' + p }),
          h('span', { style: { overflow: 'hidden', textOverflow: 'ellipsis' } }, name || 'Waiting…'),
          p === v.you && h('span', { class: 'you' }, 'you')),
        h('div', { class: 'sc' }, v.scores[p]));
    }));
  }

  function waitingBody() {
    const game = gameByKey(S.view.game);
    return h('div', {},
      h('div', { class: 'panel center' },
        h('div', { style: { fontSize: '2.2rem' } }, game.emoji),
        h('h2', { style: { margin: '6px 0 2px' } }, game.name),
        h('p', { class: 'muted small', style: { margin: '0 0 14px' } }, 'Share this with your friend to start'),
        h('div', { class: 'share-code' }, S.view.code),
        h('div', { class: 'linkbox' },
          h('code', {}, inviteLink()),
          h('button', { class: 'btn small', onclick: () => copyText(inviteLink()) }, 'Copy')),
        h('div', { class: 'btn-row', style: { marginTop: '14px' } },
          h('button', { class: 'btn primary', onclick: shareInvite }, '📤 Send invite')),
        h('p', { class: 'hint' }, h('span', { class: 'pulse' }, '● '), 'Waiting for them to join…')),
      h('div', { class: 'section-title' }, h('h2', {}, 'Change the game')),
      h('div', { class: 'grid-games' },
        S.catalog.map((g) => gameCard(g, (picked) => pickGame(picked.key)))));
  }

  function pickingBody() {
    return h('div', {},
      h('div', { class: 'section-title' },
        h('h2', {}, 'What next?'),
        h('span', { class: 'small muted' }, 'Either of you can choose')),
      h('div', { class: 'grid-games' },
        S.catalog.map((g) => gameCard(g, (picked) => pickGame(picked.key)))));
  }

  function statusLine(v, ctx) {
    const state = v.state;
    const renderer = RENDERERS[v.game];
    if (state.over) {
      const draw = state.winner === null || state.winner === undefined;
      if (draw) return { text: "It's a draw!", cls: '' };
      const won = state.winner === v.you;
      return { text: won ? '🎉 You win!' : `${v.names[state.winner]} wins`, cls: won ? 'won' : 'lost' };
    }
    if (renderer && renderer.status) {
      const custom = renderer.status(state, ctx);
      if (custom) return custom;
    }
    if (state.turn === v.you) return { text: 'Your turn', cls: 'yours' };
    if (state.turn === null || state.turn === undefined) return { text: 'Waiting…', cls: 'theirs' };
    return { text: `${v.names[state.turn]}'s turn`, cls: 'theirs' };
  }

  function playingBody() {
    const v = S.view;
    const renderer = RENDERERS[v.game];
    const ctx = {
      you: v.you,
      them: 1 - v.you,
      names: v.names,
      ui: S.ui,
      send: sendMove,
      redraw: render,
      toast,
    };
    const status = statusLine(v, ctx);

    const board = h('div', { class: 'board-wrap' });
    if (renderer) {
      try { renderer.render(board, v.state, ctx); }
      catch (err) {
        console.error(err);
        board.append(h('div', { class: 'muted' }, 'Sorry — this game failed to draw.'));
      }
    } else {
      board.append(h('div', { class: 'muted' }, 'This game is not available.'));
    }

    return h('div', {},
      h('div', { class: 'status ' + status.cls },
        h('span', {}, status.text),
        // always within reach, whatever the board's height
        h('button', {
          class: 'help', title: 'How to play', 'aria-label': 'How to play',
          onclick: () => { S.rules = v.game; render(); },
        }, '?')),
      board,
      v.state.over && gameOverBox(),
      !v.state.over && h('div', { class: 'center', style: { marginTop: '18px' } },
        h('button', {
          class: 'btn small ghost muted',
          onclick: () => {
            if (confirm('Stop this game and pick a different one?')) {
              api('/api/menu').then((r) => applyView(r.data));
            }
          },
        }, '🎮 Switch game')));
  }

  function gameOverBox() {
    const v = S.view;
    const theyWant = v.rematch[1 - v.you];
    const youWant = v.rematch[v.you];
    return h('div', { class: 'gameover' },
      h('div', { class: 'btn-row' },
        h('button', {
          class: 'btn primary', disabled: youWant, onclick: () => api('/api/rematch').then(r => applyView(r.data)),
        }, youWant ? 'Ready…' : '↻ Play again'),
        h('button', {
          class: 'btn', onclick: () => api('/api/menu').then(r => applyView(r.data)),
        }, '🎮 Another game')),
      youWant && !theyWant && h('div', { class: 'waitmark' }, `Waiting for ${v.names[1 - v.you]} to accept…`),
      theyWant && !youWant && h('div', { class: 'waitmark' }, `${v.names[1 - v.you]} wants a rematch!`));
  }

  function rulesSheet() {
    const game = gameByKey(S.rules);
    const close = () => { S.rules = null; render(); };
    return h('div', {
      class: 'backdrop',
      onclick: (e) => { if (e.target.classList.contains('backdrop')) close(); },
    },
      h('div', { class: 'sheet' },
        h('div', { style: { fontSize: '2rem', lineHeight: '1' } }, game.emoji),
        h('h2', { style: { marginTop: '8px' } }, `How to play ${game.name}`),
        h('p', { class: 'rules' }, game.rules),
        h('button', {
          class: 'btn primary wide', style: { marginTop: '18px' }, onclick: close,
        }, 'Got it')));
  }

  function roomScreen() {
    const v = S.view;
    let body;
    if (v.phase === 'waiting') body = waitingBody();
    else if (v.phase === 'picking') body = pickingBody();
    else body = playingBody();
    // a game can pin something to the foot of the screen (poker's odds bar);
    // reserve room for it so it never covers the buttons underneath
    const renderer = RENDERERS[v.game];
    const pinned = v.phase === 'playing' && renderer && renderer.bottomBar
      && v.state && !v.state.over;
    return h('div', { class: 'wrap' + (pinned ? ' has-bottom-bar' : '') },
      topbar(),
      v.phase !== 'waiting' && scorebar(),
      body,
      S.rules && rulesSheet());
  }

  async function sendMove(move) {
    const before = S.lastV;
    const res = await api('/api/move', { move });
    if (res.data && res.data.error) toast(res.data.error);
    if (res.data && res.data.v) applyView(res.data);
    // A rejected move (or a dropped connection) leaves the room exactly as it
    // was, so nothing above redraws - and a game that greys its buttons out on
    // tap would be stuck that way. Put the controls back.
    if (S.lastV === before) render();
  }

  async function pickGame(key) {
    const res = await api('/api/pick', { game: key });
    if (res.data && res.data.v) applyView(res.data);
  }

  async function leaveRoom() {
    const playing = S.view && S.view.phase === 'playing' && S.view.state && !S.view.state.over;
    if (playing && !confirm('Leave the game? This closes the room for both of you.')) return;
    await api('/api/leave');
    endSession('You left the room.');
  }

  // ---------- boot ----------

  function render() {
    // A redraw throws away the DOM, so anything being typed into would lose the
    // caret. Note what was focused and put it back afterwards.
    const active = document.activeElement;
    const keepId = active && active.id && active !== document.body ? active.id : null;
    let caret = null;
    try { caret = keepId ? active.selectionStart : null; } catch (err) { caret = null; }

    const screen = S.screen === 'room' && S.view ? roomScreen()
      : S.screen === 'join' ? joinScreen()
        : homeScreen();
    $app.replaceChildren(screen);

    if (keepId) {
      const again = document.getElementById(keepId);
      if (again && again !== document.activeElement) {
        again.focus();
        try { if (caret !== null) again.setSelectionRange(caret, caret); } catch (err) { /* not a text field */ }
      }
    }
  }

  async function init() {
    try {
      const res = await fetch('/api/games');
      S.catalog = (await res.json()).games;
    } catch (err) {
      $app.replaceChildren(h('div', { class: 'boot' }, 'Could not reach the arcade. Try refreshing.'));
      return;
    }

    const invite = (new URLSearchParams(location.search).get('room') || '').toUpperCase();
    const saved = store.load();

    if (saved && saved.room && (!invite || invite === saved.room)) {
      const res = await api('/api/resume', saved);
      if (res.ok) {
        Object.assign(S, {
          room: saved.room, player: res.data.player, token: saved.token,
          name: res.data.name, lastV: 0,
        });
        history.replaceState({}, '', '/');
        startPolling();
        return;
      }
      store.clear();
    }

    if (invite) {
      S.screen = 'join';
      S.joinCode = invite;
      render();
      peek(invite);
      return;
    }
    render();
  }

  init();
})();
