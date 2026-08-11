/* Word Ladders - both players race the same puzzle, so the board redraws while
   you are still typing. The half-typed word lives in ctx.ui so a redraw can put
   it straight back. */

(window.GAMES = window.GAMES || {}).wordladder = {
  status(v, ctx) {
    if (v.over) return null;
    return {
      text: `Turn “${v.start.toUpperCase()}” into “${v.target.toUpperCase()}”`,
      cls: 'yours',
    };
  },

  render(root, v, ctx) {
    const wrap = h('div', { style: { width: '100%', maxWidth: '420px' } });

    wrap.append(h('div', {
      style: {
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '14px',
        padding: '14px', background: 'var(--panel)', border: '1px solid var(--line)',
        borderRadius: '16px', marginBottom: '12px',
      },
    },
      chip(v.start, 'var(--muted)'),
      h('span', { class: 'muted' }, '→'),
      chip(v.target, 'var(--mint)')));

    wrap.append(h('div', { class: 'hint', style: { marginTop: '0' } },
      `A known route takes ${v.par} steps · you ${v.yourRungs} — ${v.theirRungs} ${ctx.names[1 - ctx.you]}`));

    wrap.append(ladder(v.yourLadder, 'Your ladder'));

    if (!v.over) {
      const input = h('input', {
        id: 'ladderword', maxlength: String(v.length), placeholder: '4 letters',
        autocomplete: 'off', autocorrect: 'off', autocapitalize: 'off', spellcheck: 'false',
        value: ctx.ui.draft || '',
        style: {
          flex: '1', minWidth: '0', padding: '13px 14px', borderRadius: '12px',
          background: 'var(--bg-soft)', border: '1px solid var(--line)',
          color: 'var(--text)', letterSpacing: '.18em', textTransform: 'uppercase',
          fontWeight: '600',
        },
        oninput: (e) => {
          e.target.value = e.target.value.toLowerCase().replace(/[^a-z]/g, '');
          ctx.ui.draft = e.target.value;
        },
        onkeydown: (e) => { if (e.key === 'Enter') submit(); },
      });

      wrap.append(h('div', { style: { display: 'flex', gap: '8px', marginTop: '14px' } },
        input,
        h('button', { class: 'btn primary', onclick: submit }, 'Add')));

      wrap.append(h('div', { class: 'btn-row', style: { marginTop: '10px' } },
        h('button', {
          class: 'btn small ghost', disabled: v.yourRungs === 0,
          onclick: () => { ctx.ui.draft = ''; ctx.send({ action: 'undo' }); },
        }, '↩ Undo a step')));

      function submit() {
        const word = (ctx.ui.draft || '').trim();
        if (!word) return;
        ctx.ui.draft = '';
        ctx.send({ word });
      }
    }

    if (v.over && v.theirLadder) {
      wrap.append(ladder(v.theirLadder, `${ctx.names[1 - ctx.you]}'s ladder`));
    }

    root.append(wrap);

    function chip(word, colour) {
      return h('div', {
        style: {
          fontWeight: '700', letterSpacing: '.14em', fontSize: '1.15rem',
          color: colour, textTransform: 'uppercase',
        },
      }, word);
    }

    function ladder(words, label) {
      const box = h('div', { style: { marginTop: '14px' } },
        h('div', { class: 'small muted', style: { marginBottom: '6px' } }, label));
      words.forEach((word, step) => {
        const previous = step ? words[step - 1] : null;
        const letters = word.split('').map((letter, i) => h('span', {
          style: {
            color: letter === v.target[i] ? 'var(--mint)' : 'var(--text)',
            fontWeight: previous && letter !== previous[i] ? '800' : '500',
            textDecoration: previous && letter !== previous[i] ? 'underline' : 'none',
          },
        }, letter.toUpperCase()));
        box.append(h('div', {
          style: {
            display: 'flex', alignItems: 'center', gap: '10px',
            padding: '7px 12px', marginBottom: '4px', borderRadius: '10px',
            background: word === v.target ? 'rgba(46,230,197,.16)' : 'var(--panel)',
            border: '1px solid ' + (word === v.target ? 'var(--mint)' : 'var(--line)'),
            letterSpacing: '.22em', fontFamily: 'ui-monospace, SFMono-Regular, monospace',
          },
        },
          h('span', { class: 'small muted', style: { letterSpacing: 'normal', minWidth: '1.4em' } },
            step === 0 ? '·' : String(step)),
          h('span', {}, letters)));
      });
      return box;
    }
  },
};
