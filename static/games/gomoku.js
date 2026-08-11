(window.GAMES = window.GAMES || {}).gomoku = {
  render(root, v, ctx) {
    const N = v.size;
    const yours = v.turn === ctx.you && !v.over;
    const winning = new Set(v.line || []);

    const board = h('div', {
      class: 'board',
      style: {
        gridTemplateColumns: `repeat(${N}, 1fr)`, gap: '0', maxWidth: '460px',
        background: 'linear-gradient(160deg, #33304f, #232042)',
        border: '1px solid var(--line)', borderRadius: '12px', padding: '6px',
      },
    });

    for (let i = 0; i < N * N; i++) {
      const row = Math.floor(i / N), col = i % N;
      const owner = v.board[i];
      board.append(h('button', {
        class: AR.join([owner === null && yours && 'tap']),
        style: {
          aspectRatio: '1', background: 'none', padding: '0',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          // faint lines so it reads as a grid of intersections
          borderTop: row === 0 ? 'none' : '1px solid rgba(255,255,255,.14)',
          borderLeft: col === 0 ? 'none' : '1px solid rgba(255,255,255,.14)',
        },
        onclick: () => { if (owner === null && yours) ctx.send({ cell: i }); },
      }, owner === null ? '' : h('div', {
        class: 'disc p' + owner,
        style: {
          width: '84%',
          boxShadow: winning.has(i) ? '0 0 0 2px var(--warn)'
            : v.last === i ? '0 0 0 2px rgba(255,255,255,.7)' : 'none',
        },
      })));
    }

    root.append(h('div', {},
      board,
      h('div', { class: 'hint' }, 'Five in a row wins'),
      AR.legend(ctx)));
  },
};
