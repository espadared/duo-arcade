(window.GAMES = window.GAMES || {}).memory = {
  status(v, ctx) {
    if (v.waiting) return { text: 'Not a pair…', cls: 'theirs' };
    return null;
  },

  render(root, v, ctx) {
    const yours = v.turn === ctx.you && !v.over && !v.waiting;

    const board = AR.board(v.cols, v.rows, (i) => {
      const face = v.faces[i];
      const owner = v.matched[i];
      const faceUp = face !== null;
      return h('button', {
        class: AR.join(['cell', !faceUp && yours && 'tap']),
        style: {
          fontSize: 'clamp(1.2rem, 6vw, 2rem)', borderRadius: '10px',
          background: owner !== null
            ? (owner === 0 ? 'rgba(255,107,138,.22)' : 'rgba(76,201,255,.22)')
            : faceUp ? 'var(--panel-2)' : 'linear-gradient(150deg, #3a2a7a, #24204d)',
          borderColor: owner !== null ? AR.colour(owner) : 'var(--line)',
          opacity: owner !== null ? 0.85 : 1,
        },
        onclick: () => { if (!faceUp && yours) ctx.send({ cell: i }); },
      }, faceUp ? face : '?');
    }, { maxWidth: '440px', gap: '6px' });

    root.append(h('div', {},
      board,
      h('div', { class: 'hint' },
        `Pairs — ${ctx.names[0]} ${v.scores[0]} · ${ctx.names[1]} ${v.scores[1]}`),
      AR.legend(ctx)));
  },
};
