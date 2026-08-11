/* Poker - heads-up Texas Hold'em with a dealer running the table. */

(window.GAMES = window.GAMES || {}).poker = {
  status(v, ctx) {
    if (v.over) return null;
    const said = (v.says || '').replace('{p0}', ctx.names[0]).replace('{p1}', ctx.names[1]);
    if (v.result) return { text: said, cls: v.result.winner === ctx.you ? 'yours' : 'theirs' };
    if (v.yourTurn) {
      return { text: v.toCall > 0 ? `Your move — ${v.toCall} to call` : 'Your move', cls: 'yours' };
    }
    return { text: `${ctx.names[1 - ctx.you]} is thinking…`, cls: 'theirs' };
  },

  render(root, v, ctx) {
    const them = 1 - ctx.you;
    const wrap = h('div', { style: { width: '100%', maxWidth: '440px' } });
    const money = (n) => n.toLocaleString();

    // ---------- the dealer ----------
    const said = (v.says || '').replace('{p0}', ctx.names[0]).replace('{p1}', ctx.names[1]);
    wrap.append(h('div', {
      style: {
        display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px',
        padding: '10px 14px', borderRadius: '14px',
        background: 'linear-gradient(100deg, rgba(124,92,255,.18), rgba(255,92,157,.12))',
        border: '1px solid var(--line)',
      },
    },
      h('span', { style: { fontSize: '1.4rem' } }, '🎩'),
      h('div', {},
        h('div', { class: 'small', style: { color: 'var(--muted)' } }, 'Dealer'),
        h('div', { style: { fontSize: '.92rem' } }, said || 'Shuffling up…'))));

    wrap.append(seat(them, v.theirCards, false));

    // ---------- the middle ----------
    wrap.append(h('div', {
      style: {
        margin: '12px 0', padding: '16px 12px', borderRadius: '16px', textAlign: 'center',
        background: 'linear-gradient(160deg, #14523f, #0e3b2e)',
        border: '1px solid var(--line)',
      },
    },
      h('div', { class: 'small', style: { color: 'rgba(255,255,255,.6)' } }, 'Pot'),
      h('div', { style: { fontSize: '1.6rem', fontWeight: '700', marginBottom: '10px' } },
        money(v.pot + v.bets[0] + v.bets[1])),
      h('div', { style: { display: 'flex', gap: '5px', justifyContent: 'center', minHeight: '64px' } },
        v.board.length
          ? v.board.map((c) => card(c))
          : h('span', { class: 'small', style: { color: 'rgba(255,255,255,.45)', alignSelf: 'center' } },
            'no cards yet'))));

    wrap.append(seat(ctx.you, v.yourCards, true));

    // ---------- what you can do ----------
    if (!v.over) wrap.append(actions());

    wrap.append(h('div', { class: 'hint' },
      `Hand ${v.hand} · blinds ${v.blinds[0]}/${v.blinds[1]} · ` +
      `up again in ${v.nextLevelIn} hand${v.nextLevelIn === 1 ? '' : 's'}`));

    root.append(wrap);

    // ---------- pieces ----------

    function card(c, faceDown) {
      if (faceDown || !c) {
        return h('div', {
          style: {
            width: '42px', height: '60px', borderRadius: '7px', flex: '0 0 auto',
            background: 'repeating-linear-gradient(45deg,#3a2a7a,#3a2a7a 5px,#2b2059 5px,#2b2059 10px)',
            border: '1px solid var(--line)',
          },
        });
      }
      const red = c.s === '♥' || c.s === '♦';
      return h('div', {
        style: {
          width: '42px', height: '60px', borderRadius: '7px', flex: '0 0 auto',
          background: '#f7f7fb', color: red ? '#d92d4b' : '#16182b',
          border: '1px solid #d5d6e3', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', fontWeight: '700', lineHeight: '1.05',
        },
      }, h('span', { style: { fontSize: '.95rem' } }, c.r), h('span', {}, c.s));
    }

    function seat(player, cards, isYou) {
      const acting = v.turn === player && !v.result;
      const result = v.result;
      const handLabel = result && result.names && result.showCards ? result.names[player] : null;
      return h('div', {
        style: {
          padding: '12px 14px', borderRadius: '16px', background: 'var(--panel)',
          border: '1px solid ' + (acting ? AR.colour(player) : 'var(--line)'),
          opacity: v.folded[player] ? 0.55 : 1,
        },
      },
        h('div', {
          style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' },
        },
          h('div', { style: { minWidth: 0 } },
            h('div', { style: { fontWeight: '650', color: AR.colour(player) } },
              ctx.names[player] + (isYou ? ' (you)' : ''),
              player === v.button && h('span', { class: 'pill', style: { marginLeft: '6px' } }, 'D')),
            h('div', { class: 'small muted' },
              money(v.stacks[player]) + ' chips'
              + (v.allIn[player] ? ' · ALL IN' : '')
              + (v.folded[player] ? ' · folded' : ''))),
          h('div', { style: { display: 'flex', gap: '5px' } },
            (cards || [null, null]).map((c) => card(c, !cards)))),
        (v.bets[player] > 0 || handLabel) && h('div', {
          style: { marginTop: '8px', display: 'flex', justifyContent: 'space-between', fontSize: '.82rem' },
        },
          h('span', { class: 'muted' }, handLabel || ''),
          v.bets[player] > 0 && h('span', { style: { color: 'var(--warn)' } }, 'bet ' + money(v.bets[player]))));
    }

    function actions() {
      const box = h('div', { style: { marginTop: '14px' } });
      if (!v.yourTurn) {
        return h('div', { class: 'hint', style: { marginTop: '14px' } },
          v.result ? 'Next hand shortly…' : 'Waiting for them…');
      }

      box.append(h('div', { class: 'btn-row' },
        h('button', { class: 'btn', onclick: () => ctx.send({ action: 'fold' }) }, '🏳️ Fold'),
        v.canCheck
          ? h('button', { class: 'btn primary', onclick: () => ctx.send({ action: 'check' }) }, '✓ Check')
          : h('button', {
            class: 'btn primary', onclick: () => ctx.send({ action: 'call' }),
          }, `Call ${money(v.toCall)}`)));

      // raise sizes worth offering, skipping any that collide or don't fit
      const inPlay = v.pot + v.bets[0] + v.bets[1];
      const highest = Math.max(v.bets[0], v.bets[1]);
      const options = [
        ['Min', v.minRaiseTo],
        ['½ pot', highest + Math.round(inPlay / 2)],
        ['Pot', highest + inPlay],
        ['All in', v.maxRaiseTo],
      ];
      const seen = new Set();
      const usable = [];
      for (const [label, raw] of options) {
        const to = Math.min(Math.max(raw, v.minRaiseTo), v.maxRaiseTo);
        if (to <= highest || seen.has(to)) continue;
        seen.add(to);
        usable.push([label, to]);
      }
      if (usable.length) {
        box.append(h('div', { class: 'btn-row', style: { marginTop: '8px' } },
          usable.map(([label, to]) => h('button', {
            class: 'btn small',
            // share one row rather than wrapping the last one onto its own line
            style: { flex: '1 1 0', minWidth: '0', padding: '9px 6px' },
            onclick: () => ctx.send({ action: 'raise', to }),
          }, h('span', {},
            label, h('br'),
            h('span', { class: 'muted', style: { fontSize: '.76rem' } }, money(to)))))));
      }
      return box;
    }
  },
};
