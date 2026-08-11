(window.GAMES = window.GAMES || {}).blackjack = {
  status(v, ctx) {
    if (v.over) return null;
    if (v.result) {
      const text = v.result.reason
        .replace('{p0}', ctx.names[0]).replace('{p1}', ctx.names[1]);
      const won = v.result.winner === ctx.you;
      const drew = v.result.winner === null;
      return { text: (drew ? '🤝 ' : won ? '🎉 You win the round! ' : '') + text, cls: won ? 'yours' : 'theirs' };
    }
    if (v.turn === ctx.you) return { text: `Your move — you're on ${v.yourTotal}`, cls: 'yours' };
    return { text: `${ctx.names[1 - ctx.you]} is deciding…`, cls: 'theirs' };
  },

  render(root, v, ctx) {
    const wrap = h('div', { style: { width: '100%', maxWidth: '440px' } });
    const acting = v.turn === ctx.you && !v.result && !v.over;

    wrap.append(hand(ctx.names[1 - ctx.you], v.theirCards, v.theirTotal, 1 - ctx.you,
      v.showdown, v.theirDone && !v.showdown));
    wrap.append(h('div', { class: 'hint', style: { margin: '10px 0' } },
      `Round ${v.round} of ${v.bestOf} · first to ${v.needed} · ` +
      `${ctx.names[0]} ${v.wins[0]} — ${v.wins[1]} ${ctx.names[1]}`));
    wrap.append(hand(ctx.names[ctx.you] + ' (you)', v.yourCards, v.yourTotal, ctx.you, true,
      v.yourDone && !v.showdown));

    if (!v.over) {
      wrap.append(h('div', { class: 'btn-row', style: { marginTop: '16px' } },
        h('button', {
          class: 'btn primary', disabled: !acting,
          onclick: () => ctx.send({ action: 'hit' }),
        }, '➕ Hit'),
        h('button', {
          class: 'btn', disabled: !acting,
          onclick: () => ctx.send({ action: 'stand' }),
        }, '✋ Stand')));
    }

    root.append(wrap);

    function card(c) {
      if (c.hidden) {
        return h('div', {
          style: {
            width: '46px', height: '64px', borderRadius: '8px', flex: '0 0 auto',
            background: 'repeating-linear-gradient(45deg, #3a2a7a, #3a2a7a 5px, #2b2059 5px, #2b2059 10px)',
            border: '1px solid var(--line)',
          },
        });
      }
      const red = c.s === '♥' || c.s === '♦';
      return h('div', {
        style: {
          width: '46px', height: '64px', borderRadius: '8px', flex: '0 0 auto',
          background: '#f7f7fb', color: red ? '#d92d4b' : '#16182b',
          border: '1px solid #d5d6e3', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', fontWeight: '700', lineHeight: '1.1',
        },
      }, h('span', { style: { fontSize: '1rem' } }, c.r), h('span', {}, c.s));
    }

    function hand(name, cards, total, player, showTotal, stood) {
      return h('div', {
        style: {
          padding: '14px', borderRadius: '16px', background: 'var(--panel)',
          border: '1px solid ' + (v.turn === player && !v.result ? AR.colour(player) : 'var(--line)'),
        },
      },
        h('div', {
          style: { display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '10px' },
        },
          h('span', { style: { fontWeight: '650', color: AR.colour(player) } }, name),
          h('span', { class: 'small muted' },
            (showTotal ? (total > 21 ? `BUST · ${total}` : total) : `${total} + ?`) +
            (stood ? ' · standing' : ''))),
        h('div', { style: { display: 'flex', gap: '6px', flexWrap: 'wrap' } }, cards.map(card)));
    }
  },
};
