(window.GAMES = window.GAMES || {}).tictactoe = {
  render(root, v, ctx) {
    const marks = ['✕', '◯'];
    const yours = v.turn === ctx.you && !v.over;

    const board = AR.board(3, 3, (i) => {
      const owner = v.board[i];
      const winning = v.line && v.line.indexOf(i) !== -1;
      return h('button', {
        class: AR.join(['cell', owner === null && yours && 'tap', winning && 'win']),
        style: { fontSize: '2.4rem', fontWeight: '300', color: owner === null ? '' : AR.colour(owner) },
        onclick: () => { if (owner === null && yours) ctx.send({ cell: i }); },
      }, owner === null ? '' : marks[owner]);
    }, { maxWidth: '300px', gap: '8px' });

    root.append(h('div', {}, board, AR.legend(ctx, marks)));
  },
};
