/* Tiny helpers shared by the shell and every game renderer. */

window.h = function h(tag, props, ...kids) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === 'class') el.className = value;
    else if (key === 'html') el.innerHTML = value;
    else if (key === 'style' && typeof value === 'object') Object.assign(el.style, value);
    else if (key.startsWith('on')) el.addEventListener(key.slice(2).toLowerCase(), value);
    else el.setAttribute(key, value === true ? '' : value);
  }
  for (const kid of kids.flat(9)) {
    if (kid === null || kid === undefined || kid === false || kid === '') continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
};

window.AR = {
  /* A square grid of `cols` x `rows`, filling each cell with cellFn(index). */
  board(cols, rows, cellFn, opts) {
    const options = opts || {};
    const el = h('div', {
      class: 'board ' + (options.class || ''),
      style: {
        gridTemplateColumns: `repeat(${cols}, 1fr)`,
        gap: options.gap || '4px',
        maxWidth: options.maxWidth || '460px',
      },
    });
    for (let i = 0; i < cols * rows; i++) el.append(cellFn(i));
    return el;
  },

  /* Board games are stored one way round; each player sees their own side
     at the bottom. This maps a screen position to a board index. */
  orient(index, total, flip) {
    return flip ? total - 1 - index : index;
  },

  join(list) {
    return list.filter(Boolean).join(' ');
  },

  /* "● Sam (you)   ● Alex" - who is which colour. */
  legend(ctx, marks) {
    return h('div', { class: 'legend' }, [0, 1].map((p) => h('span', {},
      h('span', { class: 'swatch p' + p }),
      (marks ? marks[p] + ' ' : '') + ctx.names[p] + (p === ctx.you ? ' (you)' : ''))));
  },

  colour(player) {
    return player === 0 ? 'var(--p0)' : 'var(--p1)';
  },
};
