/* Poker - heads-up Texas Hold'em with a dealer running the table. */

/* The gap between hands is counted down in the page rather than by asking the
   server every second. The deadline is parked on the element itself, so the
   constant redrawing of the table can't lose track of it. */
function pokerTicker() {
  if (window.__pokerTick) return;
  window.__pokerTick = setInterval(() => {
    const el = document.getElementById('pokerCountdown');
    if (!el) return;
    const left = Math.ceil((Number(el.dataset.deadline) - Date.now()) / 1000);
    const shown = left > 0 ? String(left) : '·';
    if (el.textContent !== shown) el.textContent = shown;
  }, 120);
}

(window.GAMES = window.GAMES || {}).poker = {
  // tells the shell to leave room at the foot of the page for the odds bar
  bottomBar: true,

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
    // pinned to the bottom of the screen so a new player can always see how
    // they're doing without scrolling the table (the shell reserves the space)
    if (!v.over) root.append(oddsBar());

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

    function countdown() {
      // one deadline per hand, so a redraw mid-count doesn't restart it
      if (ctx.ui.countdownHand !== v.hand) {
        ctx.ui.countdownHand = v.hand;
        ctx.ui.deadline = Date.now() + v.nextIn * 1000;
      }
      pokerTicker();
      return h('div', {
        style: {
          marginTop: '14px', padding: '14px', borderRadius: '14px', textAlign: 'center',
          background: 'var(--panel)', border: '1px solid var(--line)',
        },
      },
        h('div', { class: 'small muted' }, 'Next hand in'),
        h('div', {
          id: 'pokerCountdown', 'data-deadline': String(ctx.ui.deadline),
          style: {
            fontSize: '2.4rem', fontWeight: '800', lineHeight: '1.1',
            color: 'var(--accent-2)', fontVariantNumeric: 'tabular-nums',
          },
        }, String(Math.max(1, Math.ceil(v.nextIn)))),
        h('div', { class: 'small muted' }, 'Nothing to press — the dealer is shuffling'));
    }

    function oddsBar() {
      const win = v.winChance;
      // wording matters more than the number for anyone new to poker
      const verdict = win >= 75 ? ['Very strong', 'var(--mint)']
        : win >= 55 ? ['Strong', 'var(--mint)']
          : win >= 42 ? ['About even', 'var(--warn)']
            : win >= 25 ? ['Weak', '#ff9d5c'] : ['Very weak', 'var(--p0)'];

      return h('div', {
        style: {
          position: 'fixed', left: '0', right: '0', bottom: '0', zIndex: '20',
          // nothing in here is tappable, and it can sit over the action
          // buttons on a tall screen - so let taps fall straight through it
          pointerEvents: 'none',
          padding: '10px 16px calc(10px + env(safe-area-inset-bottom))',
          background: 'rgba(12,14,26,.93)', backdropFilter: 'blur(10px)',
          borderTop: '1px solid var(--line)',
        },
      },
        h('div', { style: { maxWidth: '440px', margin: '0 auto' } },
          h('div', {
            style: {
              display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
              gap: '8px', marginBottom: '6px',
            },
          },
            h('span', { class: 'small muted' },
              v.madeHand ? `You have ${v.madeHand.toLowerCase()}` : 'Your two cards'),
            h('span', { style: { fontWeight: '700', color: verdict[1] } },
              `${win}% · ${verdict[0]}`)),
          h('div', {
            style: {
              height: '10px', borderRadius: '999px', overflow: 'hidden',
              background: 'rgba(255,255,255,.08)',
            },
          },
            h('div', {
              style: {
                width: `${win}%`, height: '100%', borderRadius: '999px',
                background: verdict[1], transition: 'width .45s ease',
              },
            })),
          h('div', { class: 'muted', style: { marginTop: '5px', fontSize: '.7rem' } },
            v.exactOdds
              ? 'Exact chance of winning, now every card is out'
              : 'Rough chance of winning against an unknown hand')));
    }

    function actions() {
      const box = h('div', { class: 'poker-actions', style: { marginTop: '14px' } });
      if (v.result) return countdown();
      if (!v.yourTurn) {
        return h('div', { class: 'hint', style: { marginTop: '14px' } }, 'Waiting for them…');
      }

      // Grey the row out the instant it's tapped. Dealing the next street takes
      // a moment, and without this the table looks unchanged for long enough
      // that people press again and get an error for their trouble.
      const play = (move) => () => {
        box.querySelectorAll('.btn').forEach((b) => { b.disabled = true; });
        ctx.send(move);
      };

      box.append(h('div', { class: 'btn-row' },
        h('button', { class: 'btn', onclick: play({ action: 'fold' }) }, '🏳️ Fold'),
        v.canCheck
          ? h('button', { class: 'btn primary', onclick: play({ action: 'check' }) }, '✓ Check')
          : h('button', {
            class: 'btn primary', onclick: play({ action: 'call' }),
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
            onclick: play({ action: 'raise', to }),
          }, h('span', {},
            label, h('br'),
            h('span', { class: 'muted', style: { fontSize: '.76rem' } }, money(to)))))));
      }
      return box;
    }
  },
};
