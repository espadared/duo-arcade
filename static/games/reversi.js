(window.GAMES = window.GAMES || {}).reversi = {
  status(v, ctx) {
    if (v.skipped === ctx.you) return { text: 'No moves for you — turn skipped', cls: 'theirs' };
    return null;
  },

  render(root, v, ctx) {
    const N = v.size;
    const yours = v.turn === ctx.you && !v.over;
    const valid = new Set(yours ? v.valid : []);

    const board = h('div', {
      class: 'board',
      style: {
        gridTemplateColumns: `repeat(${N}, 1fr)`, gap: '2px', maxWidth: '420px',
        padding: '8px', background: 'linear-gradient(160deg, #14523f, #0e3b2e)',
        border: '1px solid var(--line)', borderRadius: '14px',
      },
    });

    for (let i = 0; i < N * N; i++) {
      const owner = v.board[Math.floor(i / N)][i % N];
      const playable = valid.has(i);
      board.append(h('button', {
        class: AR.join([playable && 'tap']),
        style: {
          aspectRatio: '1', borderRadius: '4px', border: 'none', padding: '0',
          background: 'rgba(255,255,255,.06)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: v.last === i ? 'inset 0 0 0 2px var(--warn)' : 'none',
        },
        onclick: () => { if (playable) ctx.send({ cell: i }); },
      },
        owner !== null && h('div', { class: 'disc p' + owner, style: { width: '80%' } }),
        owner === null && playable && h('div', {
          style: {
            width: '26%', aspectRatio: '1', borderRadius: '50%',
            background: 'rgba(255,255,255,.4)',
          },
        })));
    }

    root.append(h('div', {},
      board,
      h('div', { class: 'hint' },
        `${ctx.names[0]} ${v.scores[0]} — ${v.scores[1]} ${ctx.names[1]}` +
        (yours ? '  ·  dots show where you can play' : '')),
      AR.legend(ctx)));
  },
};
