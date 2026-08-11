(window.GAMES = window.GAMES || {}).xiangqi = {
  status(v, ctx) {
    if (v.over || !v.check) return null;
    return v.turn === ctx.you
      ? { text: '⚠️ Your General is in check!', cls: 'yours' }
      : { text: `${ctx.names[v.turn]} is in check`, cls: 'theirs' };
  },

  render(root, v, ctx) {
    const W = v.w, H = v.h, TOTAL = W * H;
    const RED = { K: '帥', A: '仕', E: '相', H: '傌', R: '俥', C: '炮', P: '兵' };
    const BLACK = { K: '將', A: '士', E: '象', H: '馬', R: '車', C: '砲', P: '卒' };
    const yours = v.turn === ctx.you && !v.over;
    const moves = v.moves || {};

    if (ctx.ui.sel !== undefined && !moves[String(ctx.ui.sel)]) ctx.ui.sel = undefined;
    const selected = ctx.ui.sel;
    const targets = new Set(selected === undefined ? [] : moves[String(selected)]);

    const wrap = h('div', { style: { width: '100%', maxWidth: '400px' } });
    const stage = h('div', {
      style: {
        position: 'relative', width: '100%', aspectRatio: `${W} / ${H}`,
        background: 'linear-gradient(160deg, #3d3054, #2a2140)',
        border: '1px solid var(--line)', borderRadius: '10px', padding: '0',
      },
      html: boardSvg(),
    });

    const grid = h('div', {
      style: {
        position: 'absolute', inset: '0', display: 'grid',
        gridTemplateColumns: `repeat(${W}, 1fr)`, gridTemplateRows: `repeat(${H}, 1fr)`,
      },
    });

    for (let screen = 0; screen < TOTAL; screen++) {
      const idx = AR.orient(screen, TOTAL, v.flip);
      const piece = v.board[idx];
      const isRed = piece && piece.o === v.red;
      const isTarget = targets.has(idx);
      const canPick = yours && piece && piece.o === ctx.you && moves[String(idx)];
      const isSel = selected === idx;
      const isLast = v.last && (v.last[0] === idx || v.last[1] === idx);

      grid.append(h('button', {
        class: AR.join([(canPick || isTarget) && 'tap']),
        style: {
          background: 'none', border: 'none', padding: '0',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        },
        onclick: () => {
          if (!yours) return;
          if (isTarget) { ctx.ui.sel = undefined; ctx.send({ from: selected, to: idx }); return; }
          if (canPick) { ctx.ui.sel = isSel ? undefined : idx; ctx.redraw(); return; }
          ctx.ui.sel = undefined; ctx.redraw();
        },
      },
        piece && h('div', {
          style: {
            width: '88%', aspectRatio: '1', borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 'clamp(.75rem, 4.4vw, 1.4rem)', fontWeight: '700',
            background: 'radial-gradient(circle at 35% 28%, #fdf3dc, #e3cda1)',
            color: isRed ? '#c62828' : '#1c1c22',
            border: `2px solid ${isRed ? '#c62828' : '#1c1c22'}`,
            boxShadow: isSel ? '0 0 0 3px var(--mint)'
              : isTarget ? '0 0 0 3px var(--warn)'        // a piece you can capture
                : isLast ? '0 0 0 3px rgba(255,204,102,.6)'
                  : '0 2px 5px rgba(0,0,0,.5)',
          },
        }, (isRed ? RED : BLACK)[piece.p]),
        !piece && isTarget && h('div', {
          style: {
            width: '26%', aspectRatio: '1', borderRadius: '50%',
            background: 'rgba(46,230,197,.9)',
          },
        })));
    }

    stage.append(grid);
    wrap.append(stage);
    wrap.append(h('div', { class: 'hint' },
      `${ctx.you === v.red ? 'You are Red — you moved first' : 'You are Black'}` +
      (yours && selected === undefined ? '  ·  tap a piece to see its moves' : '')));
    wrap.append(AR.legend(ctx));
    root.append(wrap);

    function boardSvg() {
      const X = (c) => (c + 0.5).toFixed(2);
      const Y = (r) => (r + 0.5).toFixed(2);
      const lines = [];
      for (let r = 0; r < H; r++) lines.push(`<line x1="${X(0)}" y1="${Y(r)}" x2="${X(W - 1)}" y2="${Y(r)}"/>`);
      for (let c = 0; c < W; c++) {
        if (c === 0 || c === W - 1) {
          lines.push(`<line x1="${X(c)}" y1="${Y(0)}" x2="${X(c)}" y2="${Y(H - 1)}"/>`);
        } else {
          // the river splits every inner file in two
          lines.push(`<line x1="${X(c)}" y1="${Y(0)}" x2="${X(c)}" y2="${Y(4)}"/>`);
          lines.push(`<line x1="${X(c)}" y1="${Y(5)}" x2="${X(c)}" y2="${Y(9)}"/>`);
        }
      }
      for (const [top, bottom] of [[0, 2], [7, 9]]) {
        lines.push(`<line x1="${X(3)}" y1="${Y(top)}" x2="${X(5)}" y2="${Y(bottom)}"/>`);
        lines.push(`<line x1="${X(5)}" y1="${Y(top)}" x2="${X(3)}" y2="${Y(bottom)}"/>`);
      }
      return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"
        style="position:absolute;inset:0;width:100%;height:100%">
        <g stroke="rgba(255,255,255,.38)" stroke-width="0.028" fill="none"
           stroke-linecap="round">${lines.join('')}</g>
        <text x="2.5" y="5.18" fill="rgba(255,255,255,.3)" font-size="0.46"
              text-anchor="middle" letter-spacing="0.1">楚 河</text>
        <text x="6.5" y="5.18" fill="rgba(255,255,255,.3)" font-size="0.46"
              text-anchor="middle" letter-spacing="0.1">漢 界</text>
      </svg>`;
    }
  },
};
