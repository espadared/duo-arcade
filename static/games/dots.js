(window.GAMES = window.GAMES || {}).dots = {
  render(root, v, ctx) {
    const N = v.size;
    const yours = v.turn === ctx.you && !v.over;
    const DOT = '11px';

    const board = h('div', {
      style: {
        display: 'grid',
        gridTemplateColumns: `repeat(${N}, ${DOT} minmax(0,1fr)) ${DOT}`,
        gridTemplateRows: `repeat(${N}, ${DOT} minmax(0,1fr)) ${DOT}`,
        width: '100%', maxWidth: '400px', margin: '0 auto', aspectRatio: '1',
        padding: '10px', background: 'var(--panel)',
        border: '1px solid var(--line)', borderRadius: '14px',
      },
    });

    const drawn = (owner) => owner === null ? 'rgba(255,255,255,.10)' : AR.colour(owner);

    for (let gr = 0; gr <= 2 * N; gr++) {
      for (let gc = 0; gc <= 2 * N; gc++) {
        const rowEven = gr % 2 === 0, colEven = gc % 2 === 0;

        if (rowEven && colEven) {
          board.append(h('div', {
            style: {
              alignSelf: 'center', justifySelf: 'center',
              width: '7px', height: '7px', borderRadius: '50%', background: 'var(--muted)',
            },
          }));
          continue;
        }

        const horizontal = rowEven;
        const r = horizontal ? gr / 2 : (gr - 1) / 2;
        const c = horizontal ? (gc - 1) / 2 : gc / 2;

        if (rowEven !== colEven) {
          const owner = horizontal ? v.h[r][c] : v.v[r][c];
          const free = owner === null && yours;
          board.append(h('button', {
            class: AR.join([free && 'tap']),
            style: {
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              padding: horizontal ? '0 1px' : '1px 0', background: 'none', border: 'none',
            },
            onclick: () => { if (free) ctx.send({ t: horizontal ? 'h' : 'v', r, c }); },
          }, h('div', {
            style: {
              width: horizontal ? '100%' : '5px',
              height: horizontal ? '5px' : '100%',
              borderRadius: '3px', background: drawn(owner),
              transition: 'background .15s ease',
            },
          })));
          continue;
        }

        // both odd - the middle of a box
        const owner = v.boxes[(gr - 1) / 2][(gc - 1) / 2];
        board.append(h('div', {
          style: {
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 'clamp(.6rem, 3vw, .95rem)', fontWeight: '700',
            color: owner === null ? 'transparent' : '#fff',
            background: owner === null ? 'transparent'
              : owner === 0 ? 'rgba(255,107,138,.28)' : 'rgba(76,201,255,.28)',
            borderRadius: '4px',
          },
        }, owner === null ? '' : ctx.names[owner].slice(0, 1).toUpperCase()));
      }
    }

    root.append(h('div', {},
      board,
      h('div', { class: 'hint' },
        `Boxes — ${ctx.names[0]} ${v.scores[0]} · ${ctx.names[1]} ${v.scores[1]}` +
        (yours ? '  ·  tap a gap to draw a line' : '')),
      AR.legend(ctx)));
  },
};
