(window.GAMES = window.GAMES || {}).connect4 = {
  render(root, v, ctx) {
    const COLS = 7, ROWS = 6;
    const yours = v.turn === ctx.you && !v.over;
    const winning = new Set((v.line || []).map((cell) => cell[0] * COLS + cell[1]));
    const full = (col) => v.grid[0][col] !== null;

    const board = h('div', {
      class: 'board',
      style: {
        gridTemplateColumns: `repeat(${COLS}, 1fr)`,
        gap: '5px', maxWidth: '420px', padding: '8px',
        background: 'linear-gradient(160deg, #2a3468, #1b2145)',
        border: '1px solid var(--line)', borderRadius: '16px',
      },
    });

    for (let row = 0; row < ROWS; row++) {
      for (let col = 0; col < COLS; col++) {
        const owner = v.grid[row][col];
        const isLast = v.last && v.last[0] === row && v.last[1] === col;
        board.append(h('button', {
          class: AR.join(['cell', yours && !full(col) && 'tap']),
          style: {
            borderRadius: '50%', background: 'rgba(6,8,20,.55)', border: 'none',
            boxShadow: winning.has(row * COLS + col) ? '0 0 0 3px var(--warn)'
              : isLast ? '0 0 0 2px rgba(255,255,255,.35)' : 'none',
          },
          onclick: () => { if (yours && !full(col)) ctx.send({ col }); },
        }, owner === null ? '' : h('div', { class: 'disc p' + owner, style: { width: '86%' } })));
      }
    }

    root.append(h('div', {},
      board,
      h('div', { class: 'hint' }, yours ? 'Tap a column to drop your disc' : ''),
      AR.legend(ctx)));
  },
};
