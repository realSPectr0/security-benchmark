(function() {
    let lastPaste = 0;
    document.addEventListener('paste', (e) => {
        if (e.target.id === 'challenge-input') lastPaste = Date.now();
    });
    const oldFetch = window.fetch;
    window.fetch = function() {
        if (arguments[0] && arguments[0].includes('/api/v1/challenges/attempt')) {
            try {
                let init = arguments[1];
                let body = JSON.parse(init.body);
                body.paste_diff = lastPaste ? (Date.now() - lastPaste) : -1;
                init.body = JSON.stringify(body);
            } catch (e) {}
        }
        return oldFetch.apply(this, arguments);
    };
})();
