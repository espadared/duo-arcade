/* Crosswires (Bridg-It) - two interleaved lattices of posts on one CSS grid.

   (even row, odd  col)  post belonging to player 0
   (odd  row, even col)  post belonging to player 1
   anything else         a gap that can hold exactly one wire
*/

(window.GAMES = window.GAMES || {}).crosswires = {
  render(root, v, ctx) {
    const SPAN = v.span;
    const yours = v.turn === ctx.you && !v.over;
    const mine = new Set((v.yours || []).map(([r, c]) => r * 1000 + c));
    const last = v.last ? v.last[0] * 1000 + v.last[1] : -1;

    const board = h('div', {
      style: {
        display: 'grid',
        gridTemplateColumns: `repeat(${SPAN + 1}, minmax(0, 1fr))`,
        gridTemplateRows: `repeat(${SPAN + 1}, minmax(0, 1fr))`,
        width: '100%', maxWidth: '400px', margin: '0 auto', aspectRatio: '1',
        padding: '10px', background: 'var(--panel)',
        border: '1px solid var(--line)', borderRadius: '14px',
      },
    });

    const post = (owner) => h('div', {
      style: {
        alignSelf: 'center', justifySelf: 'center',
        width: '58%', aspectRatio: '1', borderRadius: '50%',
        background: owner === 0 ? 'rgba(255,107,138,.55)' : 'rgba(76,201,255,.55)',
      },
    });

    const wire = (owner, horizontal, highlight) => h('div', {
      style: {
        alignSelf: 'center', justifySelf: 'center',
        width: horizontal ? '112%' : '34%',
        height: horizontal ? '34%' : '112%',
        borderRadius: '3px',
        background: AR.colour(owner),
        boxShadow: highlight ? '0 0 0 2px var(--warn)' : 'none',
      },
    });

    for (let r = 0; r <= SPAN; r++) {
      for (let c = 0; c <= SPAN; c++) {
        const rowEven = r % 2 === 0, colEven = c % 2 === 0;

        if (rowEven !== colEven) {                 // a post, not a gap
          board.append(post(rowEven ? 0 : 1));
          continue;
        }

        const owner = v.grid[r][c];
        if (owner !== null) {
          // player 0 lays horizontal wires on even rows, vertical on odd rows
          const horizontal = owner === 0 ? rowEven : !rowEven;
          board.append(h('div', { style: { display: 'grid' } },
            wire(owner, horizontal, last === r * 1000 + c)));
          continue;
        }

        const free = yours && mine.has(r * 1000 + c);
        board.append(h('button', {
          class: AR.join([free && 'tap']),
          style: {
            background: 'none', border: 'none', padding: '0',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: free ? 'pointer' : 'default',
          },
          onclick: () => { if (free) ctx.send({ r, c }); },
        }, free && h('div', {
          style: {
            width: '30%', aspectRatio: '1', borderRadius: '50%',
            background: 'rgba(255,255,255,.22)',
          },
        })));
      }
    }

    const goal = ctx.you === 0 ? 'top to bottom' : 'left to right';
    root.append(h('div', {},
      board,
      h('div', { class: 'hint' },
        `You're wiring ${goal}` + (yours ? '  ·  tap a dot to lay a wire' : '')),
      AR.legend(ctx)));
  },
};
