(window.GAMES = window.GAMES || {}).battleship = {
  status(v, ctx) {
    if (v.over) return null;
    if (v.phase === 'place') {
      return v.youReady
        ? { text: 'Fleet ready — waiting for them to place theirs…', cls: 'theirs' }
        : { text: 'Place your fleet', cls: 'yours' };
    }
    if (v.sunkNote) {
      const bySelf = v.sunkNote.player === ctx.you;
      return {
        text: (bySelf ? '💥 You sank their ' : '🔥 They sank your ') + v.sunkNote.ship + '!',
        cls: bySelf ? 'yours' : 'theirs',
      };
    }
    return null;
  },

  render(root, v, ctx) {
    const N = v.size;
    const wrap = h('div', { style: { width: '100%', maxWidth: '420px' } });

    if (v.phase === 'place') renderPlacing();
    else renderFiring();

    root.append(wrap);

    // ---------- putting your ships out ----------

    function cellsFor(row, col, len, dir) {
      if (dir === 'h') {
        if (col + len > N) return null;
        return Array.from({ length: len }, (_, i) => row * N + col + i);
      }
      if (row + len > N) return null;
      return Array.from({ length: len }, (_, i) => (row + i) * N + col);
    }

    function layoutCells(placements) {
      const used = new Map();
      placements.forEach((spot, shipIndex) => {
        const cells = cellsFor(spot[0], spot[1], v.spec[shipIndex].len, spot[2]);
        (cells || []).forEach((cell) => used.set(cell, shipIndex));
      });
      return used;
    }

    function randomLayout() {
      for (let attempt = 0; attempt < 200; attempt++) {
        const placements = [];
        const used = new Set();
        let ok = true;
        for (const ship of v.spec) {
          let placed = false;
          for (let tries = 0; tries < 300 && !placed; tries++) {
            const dir = Math.random() < 0.5 ? 'h' : 'v';
            const row = Math.floor(Math.random() * N);
            const col = Math.floor(Math.random() * N);
            const cells = cellsFor(row, col, ship.len, dir);
            if (cells && !cells.some((c) => used.has(c))) {
              cells.forEach((c) => used.add(c));
              placements.push([row, col, dir]);
              placed = true;
            }
          }
          if (!placed) { ok = false; break; }
        }
        if (ok) return placements;
      }
      return [];
    }

    function renderPlacing() {
      if (!ctx.ui.placements) { ctx.ui.placements = []; ctx.ui.dir = 'h'; }
      const placements = ctx.ui.placements;
      const used = layoutCells(placements);
      const nextShip = v.spec[placements.length];
      const done = placements.length === v.spec.length;

      if (v.youReady) {
        wrap.append(h('div', { class: 'panel center' },
          h('div', { style: { fontSize: '2rem' } }, '⚓'),
          h('p', {}, 'Your fleet is hidden and ready.'),
          h('p', { class: 'hint' }, h('span', { class: 'pulse' }, '● '),
            `Waiting for ${ctx.names[1 - ctx.you]} to place their ships…`)));
        wrap.append(ownGrid(used, true));
        return;
      }

      wrap.append(h('div', { class: 'panel', style: { padding: '14px', marginBottom: '12px' } },
        h('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' } },
          h('div', {},
            h('div', { style: { fontWeight: '650' } },
              done ? 'All ships placed!' : `Place your ${nextShip.name}`),
            h('div', { class: 'small muted' },
              done ? 'Happy with it? Lock it in.' : `${nextShip.len} squares · pointing ${ctx.ui.dir === 'h' ? 'across →' : 'down ↓'}`)),
          !done && h('button', {
            class: 'btn small',
            onclick: () => { ctx.ui.dir = ctx.ui.dir === 'h' ? 'v' : 'h'; ctx.redraw(); },
          }, '⟳ Rotate'))));

      wrap.append(ownGrid(used, false, (cell) => {
        if (done) { ctx.toast('All five ships are placed.'); return; }
        const row = Math.floor(cell / N), col = cell % N;
        const cells = cellsFor(row, col, nextShip.len, ctx.ui.dir);
        if (!cells) { ctx.toast("That ship won't fit there."); return; }
        if (cells.some((c) => used.has(c))) { ctx.toast('Ships cannot overlap.'); return; }
        placements.push([row, col, ctx.ui.dir]);
        ctx.redraw();
      }));

      wrap.append(h('div', { class: 'btn-row', style: { marginTop: '12px' } },
        h('button', {
          class: 'btn', disabled: !placements.length,
          onclick: () => { placements.pop(); ctx.redraw(); },
        }, '↩ Undo'),
        h('button', {
          class: 'btn',
          onclick: () => { ctx.ui.placements = randomLayout(); ctx.redraw(); },
        }, '🎲 Random'),
        h('button', {
          class: 'btn primary', disabled: !done,
          onclick: () => ctx.send({ action: 'place', ships: placements }),
        }, '⚓ Ready')));
    }

    function ownGrid(used, hideShips, onTap) {
      const grid = AR.board(N, N, (cell) => {
        const shipIndex = used.get(cell);
        const shot = v.shotsAtYou[cell];
        return h('button', {
          class: AR.join([onTap && 'tap']),
          style: {
            aspectRatio: '1', borderRadius: '3px', border: 'none', padding: '0',
            fontSize: 'clamp(.5rem, 2.4vw, .8rem)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: shot === 'hit' ? 'rgba(255,92,92,.75)'
              : shipIndex !== undefined && !hideShips ? 'rgba(76,201,255,.75)'
                : shipIndex !== undefined ? 'rgba(76,201,255,.45)'
                  : 'rgba(255,255,255,.07)',
          },
          onclick: () => onTap && onTap(cell),
        }, shot === 'hit' ? '✖' : shot === 'miss' ? '·' : '');
      }, { maxWidth: '420px', gap: '2px' });
      return h('div', {}, h('div', { class: 'small muted', style: { margin: '10px 0 6px' } },
        'Your waters'), grid);
    }

    // ---------- the hunt ----------

    function renderFiring() {
      const yours = v.turn === ctx.you && !v.over;
      const sunkCells = new Set();
      v.theirShips.forEach((ship) => { if (ship.cells) ship.cells.forEach((c) => sunkCells.add(c)); });

      const enemy = AR.board(N, N, (cell) => {
        const shot = v.shotsAtThem[cell];
        const free = yours && !shot;
        return h('button', {
          class: AR.join([free && 'tap']),
          style: {
            aspectRatio: '1', borderRadius: '3px', border: 'none', padding: '0',
            fontSize: 'clamp(.55rem, 2.6vw, .9rem)', fontWeight: '700',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: shot === 'hit' ? '#fff' : 'var(--muted)',
            background: shot === 'hit'
              ? (sunkCells.has(cell) ? 'rgba(140,20,40,.9)' : 'rgba(255,92,92,.8)')
              : shot === 'miss' ? 'rgba(255,255,255,.13)'
                : 'rgba(76,201,255,.10)',
          },
          onclick: () => { if (free) ctx.send({ action: 'fire', cell }); },
        }, shot === 'hit' ? '✖' : shot === 'miss' ? '•' : '');
      }, { maxWidth: '420px', gap: '2px' });

      wrap.append(h('div', { class: 'small muted', style: { marginBottom: '6px' } },
        `${ctx.names[1 - ctx.you]}'s waters` + (yours ? ' — tap to fire' : '')));
      wrap.append(enemy);
      wrap.append(fleetRow(v.theirShips, 'Their fleet'));

      const used = new Map();
      v.yourShips.forEach((ship, i) => ship.cells.forEach((c) => used.set(c, i)));
      wrap.append(ownGrid(used, false));
      wrap.append(fleetRow(v.yourShips, 'Your fleet'));
    }

    function fleetRow(ships, label) {
      return h('div', { style: { display: 'flex', gap: '6px', flexWrap: 'wrap', margin: '8px 0 4px' } },
        h('span', { class: 'small muted', style: { marginRight: '2px' } }, label + ':'),
        ships.map((ship) => h('span', {
          class: 'pill',
          style: {
            opacity: ship.sunk ? 1 : 0.75,
            textDecoration: ship.sunk ? 'line-through' : 'none',
            color: ship.sunk ? 'var(--p0)' : 'var(--muted)',
          },
        }, ship.name)));
    }
  },
};
