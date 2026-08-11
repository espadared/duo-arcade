(window.GAMES = window.GAMES || {}).rps = {
  status(v, ctx) {
    if (v.over) return null;
    if (v.reveal) {
      const r = v.reveal.result;
      if (r === null) return { text: "Draw — nobody scores", cls: 'theirs' };
      return r === ctx.you ? { text: 'You take the round!', cls: 'yours' }
        : { text: `${ctx.names[r]} takes the round`, cls: 'theirs' };
    }
    if (v.yourPick) return { text: 'Locked in — waiting for them…', cls: 'theirs' };
    return { text: `Round ${v.round} — choose!`, cls: 'yours' };
  },

  render(root, v, ctx) {
    const ICONS = { rock: '✊', paper: '✋', scissors: '✌️' };
    const wrap = h('div', { style: { width: '100%', maxWidth: '420px' } });

    // the two hands
    const mine = v.reveal ? v.reveal.picks[ctx.you] : v.yourPick;
    const theirs = v.reveal ? v.reveal.picks[1 - ctx.you] : null;

    wrap.append(h('div', {
      style: {
        display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center',
        gap: '10px', padding: '20px 12px', background: 'var(--panel)',
        border: '1px solid var(--line)', borderRadius: '16px', textAlign: 'center',
      },
    },
      hand(ctx.names[ctx.you] + ' (you)', mine ? ICONS[mine] : (v.yourPick ? '🔒' : '❔'), 'p' + ctx.you),
      h('div', { class: 'muted', style: { fontWeight: '700' } }, 'vs'),
      hand(ctx.names[1 - ctx.you], theirs ? ICONS[theirs] : (v.theyPicked ? '🔒' : '❔'), 'p' + (1 - ctx.you))));

    // score dots
    wrap.append(h('div', { class: 'hint' },
      `Round ${Math.min(v.round, v.bestOf)} of ${v.bestOf} · first to ${v.needed} wins · ` +
      `${ctx.names[0]} ${v.wins[0]} — ${v.wins[1]} ${ctx.names[1]}`));

    if (!v.over) {
      const locked = !!v.yourPick || !!v.reveal;
      wrap.append(h('div', { class: 'btn-row', style: { marginTop: '14px' } },
        ['rock', 'paper', 'scissors'].map((pick) => h('button', {
          class: 'btn' + (locked ? '' : ' primary'),
          disabled: locked,
          style: { flexDirection: 'column', gap: '4px', padding: '16px 8px' },
          onclick: () => ctx.send({ pick }),
        },
          h('span', { style: { fontSize: '1.8rem' } }, ICONS[pick]),
          h('span', { style: { fontSize: '.78rem' } }, pick)))));
    }

    root.append(wrap);

    function hand(name, icon, cls) {
      return h('div', {},
        h('div', { style: { fontSize: '3rem', lineHeight: '1.2' } }, icon),
        h('div', { class: 'small', style: { color: cls === 'p0' ? 'var(--p0)' : 'var(--p1)' } }, name));
    }
  },
};
