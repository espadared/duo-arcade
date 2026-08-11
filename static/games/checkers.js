(window.GAMES = window.GAMES || {}).checkers = {
  status(v, ctx) {
    if (v.over || v.turn !== ctx.you) return null;
    if (v.chain !== null && v.chain !== undefined) return { text: 'Keep jumping!', cls: 'yours' };
    const mustCapture = Object.values(v.moves).some((list) => list.some((m) => m.cap !== null));
    if (mustCapture) return { text: 'Your turn — you must capture', cls: 'yours' };
    return null;
  },

  render(root, v, ctx) {
    const N = v.size;
    const yours = v.turn === ctx.you && !v.over;
    const moves = v.moves || {};

    if (v.chain !== null && v.chain !== undefined) ctx.ui.sel = v.chain;
    if (ctx.ui.sel !== undefined && !moves[String(ctx.ui.sel)]) ctx.ui.sel = undefined;

    const selected = ctx.ui.sel;
    const targets = new Map();
    if (selected !== undefined) {
      for (const m of moves[String(selected)] || []) targets.set(m.to, m);
    }

    const board = h('div', {
      class: 'board',
      style: {
        gridTemplateColumns: `repeat(${N}, 1fr)`, gap: '0', maxWidth: '420px',
        border: '4px solid #3a2f6b', borderRadius: '12px', overflow: 'hidden',
      },
    });

    for (let screen = 0; screen < N * N; screen++) {
      const idx = AR.orient(screen, N * N, v.flip);
      const row = Math.floor(idx / N), col = idx % N;
      const playable = (row + col) % 2 === 1;
      const piece = v.board[idx];
      const isTarget = targets.has(idx);
      const isSel = selected === idx;
      const canPick = yours && piece && piece.o === ctx.you && moves[String(idx)];
      const isLast = v.last && (v.last[0] === idx || v.last[1] === idx);

      board.append(h('button', {
        class: AR.join([(canPick || isTarget) && 'tap']),
        style: {
          aspectRatio: '1', border: 'none', padding: '0',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: playable ? '#39406e' : '#20244a',
          boxShadow: isSel ? 'inset 0 0 0 3px var(--mint)'
            : isLast ? 'inset 0 0 0 2px rgba(255,204,102,.7)' : 'none',
        },
        onclick: () => {
          if (!yours) return;
          if (isTarget) { ctx.ui.sel = undefined; ctx.send({ from: selected, to: idx }); return; }
          if (canPick) { ctx.ui.sel = isSel ? undefined : idx; ctx.redraw(); return; }
          if (v.chain === null || v.chain === undefined) { ctx.ui.sel = undefined; ctx.redraw(); }
        },
      },
        piece && h('div', {
          style: {
            width: '76%', aspectRatio: '1', borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 'clamp(.8rem, 4vw, 1.3rem)', color: 'rgba(0,0,0,.55)',
            background: piece.o === 0
              ? 'radial-gradient(circle at 34% 28%, #ff9db1, #e5375f)'
              : 'radial-gradient(circle at 34% 28%, #97ddff, #1a8ec9)',
            boxShadow: '0 2px 6px rgba(0,0,0,.45), inset 0 -2px 4px rgba(0,0,0,.25)',
          },
        }, piece.k ? '♛' : ''),
        !piece && isTarget && h('div', {
          style: {
            width: '30%', aspectRatio: '1', borderRadius: '50%',
            background: targets.get(idx).cap !== null ? 'var(--warn)' : 'rgba(46,230,197,.85)',
          },
        })));
    }

    root.append(h('div', {},
      board,
      h('div', { class: 'hint' },
        `Pieces — ${ctx.names[0]} ${v.counts[0]} · ${ctx.names[1]} ${v.counts[1]}` +
        (yours && selected === undefined ? '  ·  tap one of your pieces' : '')),
      AR.legend(ctx)));
  },
};
