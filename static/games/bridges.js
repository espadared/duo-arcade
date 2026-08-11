/* Bridges (Hex) - a rhombus of hexagons, drawn as one SVG that scales to fit. */

(window.GAMES = window.GAMES || {}).bridges = {
  render(root, v, ctx) {
    const N = v.size;
    const yours = v.turn === ctx.you && !v.over;
    const winning = new Set(v.path || []);
    const W = Math.sqrt(3);                 // width of a hex whose radius is 1
    const cx = (r, c) => W * (c + r / 2) + W / 2;
    const cy = (r) => 1.5 * r + 1;
    const boardW = W * (N + (N - 1) / 2);
    const boardH = 1.5 * (N - 1) + 2;
    const PAD = 0.55;                       // room for the coloured home edges

    // vertex 0 is the top point, then clockwise: 1 upper-right, 2 lower-right,
    // 3 bottom, 4 lower-left, 5 upper-left
    const vertex = (r, c, k) => {
      const a = (Math.PI / 180) * (60 * k - 90);
      return `${(cx(r, c) + Math.cos(a)).toFixed(3)},${(cy(r) + Math.sin(a)).toFixed(3)}`;
    };
    const hexPoints = (r, c) =>
      [0, 1, 2, 3, 4, 5].map((k) => vertex(r, c, k)).join(' ');

    // Trace the real hex edges along each side, so nothing pokes out past the
    // coloured border the way a straight corner-to-corner line would allow.
    const side = (steps) => steps.join(' ');
    const topEdge = side([].concat(...Array.from({ length: N }, (_, c) =>
      [vertex(0, c, 5), vertex(0, c, 0), vertex(0, c, 1)])));
    const bottomEdge = side([].concat(...Array.from({ length: N }, (_, c) =>
      [vertex(N - 1, c, 4), vertex(N - 1, c, 3), vertex(N - 1, c, 2)])));
    const leftEdge = side([].concat(...Array.from({ length: N }, (_, r) =>
      [vertex(r, 0, 5), vertex(r, 0, 4), vertex(r, 0, 3)])));
    const rightEdge = side([].concat(...Array.from({ length: N }, (_, r) =>
      [vertex(r, N - 1, 0), vertex(r, N - 1, 1), vertex(r, N - 1, 2)])));

    const cells = [];
    for (let i = 0; i < N * N; i++) {
      const r = Math.floor(i / N), c = i % N;
      const owner = v.board[i];
      const fill = owner === null ? 'rgba(255,255,255,.07)'
        : owner === 0 ? '#ff6b8a' : '#4cc9ff';
      const stroke = winning.has(i) ? '#ffcc66'
        : v.last === i ? 'rgba(255,255,255,.85)' : 'rgba(255,255,255,.22)';
      const strokeW = (winning.has(i) || v.last === i) ? 0.14 : 0.05;
      cells.push(
        `<polygon data-i="${i}" points="${hexPoints(r, c)}" fill="${fill}"` +
        ` stroke="${stroke}" stroke-width="${strokeW}"` +
        ` style="cursor:${owner === null && yours ? 'pointer' : 'default'}"/>`);
    }

    const border = (points, colour) =>
      `<polyline points="${points}" fill="none" stroke="${colour}"` +
      ` stroke-width="0.26" stroke-linecap="round" stroke-linejoin="round"/>`;

    const stage = h('div', {
      style: { width: '100%', maxWidth: '460px', margin: '0 auto' },
      html:
        `<svg viewBox="${-PAD} ${-PAD} ${boardW + PAD * 2} ${boardH + PAD * 2}"
              style="width:100%;height:auto;display:block">
          ${cells.join('')}
          ${border(topEdge, '#ff6b8a')}${border(bottomEdge, '#ff6b8a')}
          ${border(leftEdge, '#4cc9ff')}${border(rightEdge, '#4cc9ff')}
        </svg>`,
    });

    stage.addEventListener('click', (event) => {
      if (!yours) return;
      const hit = event.target.closest('[data-i]');
      if (!hit) return;
      const cell = Number(hit.getAttribute('data-i'));
      if (v.board[cell] === null) ctx.send({ cell });
    });

    const goal = ctx.you === 0 ? 'top edge to the bottom edge'
      : 'left edge to the right edge';
    root.append(h('div', {},
      stage,
      h('div', { class: 'hint' }, `You're joining the ${goal}`),
      AR.legend(ctx)));
  },
};
