(function () {
    const initialTheme = document.documentElement.getAttribute('data-initial-theme') || 'auto';

    function applyTheme(theme) {
        if (theme === 'auto') {
            const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
    }

    function setupTheme() {
        const savedTheme = localStorage.getItem('report-theme');
        if (savedTheme) {
            applyTheme(savedTheme);
        } else {
            applyTheme(initialTheme);
        }

        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                localStorage.setItem('report-theme', newTheme);
                applyTheme(newTheme);
            });
        }

        try {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
                const saved = localStorage.getItem('report-theme');
                if (!saved || saved === 'auto') {
                    applyTheme('auto');
                }
            });
        } catch (e) { console.error("matchMedia listener not supported", e); }
    }

    function init() {
        const q = (sel, el = document) => el.querySelector(sel);
        const qa = (sel, el = document) => Array.from(el.querySelectorAll(sel));
        const filters = new Set();
        let currentlyOpenId = null;

        function toggleRow(tr, multi) {
            const id = tr.getAttribute('aria-controls');
            if (!id) return;
            const panel = document.getElementById(id);
            const expanded = tr.getAttribute('aria-expanded') === 'true';
            if (!multi && currentlyOpenId && currentlyOpenId !== id) {
                const prevTr = document.querySelector(`tr.test-row[aria-controls="${currentlyOpenId}"]`);
                if (prevTr) {
                    prevTr.setAttribute('aria-expanded', 'false');
                    const prevPanel = document.getElementById(currentlyOpenId);
                    if (prevPanel) prevPanel.hidden = true;
                }
            }
            tr.setAttribute('aria-expanded', !expanded);
            if (panel) panel.hidden = expanded;
            currentlyOpenId = expanded ? null : id;
        }
        qa('tbody tr.test-row').forEach(tr => {
            tr.addEventListener('click', (e) => toggleRow(tr, e.altKey === true));
            tr.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleRow(tr, e.altKey === true); } });
        });

        const searchInput = q('#search');
        let searchTerm = '';
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                searchTerm = e.target.value.toLowerCase();
                applyFilters();
            });
        }

        const filterCards = qa('.card[data-filter]');
        filterCards.forEach(card => {
            card.addEventListener('click', () => {
                const filter = card.dataset.filter;
                if (filter === 'all') {
                    filters.clear();
                } else {
                    if (filters.has(filter)) {
                        filters.delete(filter);
                    } else {
                        filters.add(filter);
                    }
                }
                applyFilters();
                updateCardStyles();
            });
        });

        function applyFilters() {
            qa('tbody tr.test-row').forEach(row => {
                const status = row.dataset.status;
                const text = (row.dataset.text || '').toLowerCase();
                const statusMatch = filters.size === 0 || filters.has(status);
                const searchMatch = !searchTerm || text.includes(searchTerm);
                const shouldShow = statusMatch && searchMatch;
                row.style.display = shouldShow ? '' : 'none';
                const detailsRow = document.getElementById(row.getAttribute('aria-controls'));
                if (detailsRow) {
                    detailsRow.style.display = shouldShow ? '' : 'none';
                }
            });
        }

        function updateCardStyles() {
            let activeCardFound = false;
            filterCards.forEach(card => {
                const filter = card.dataset.filter;
                if (filters.has(filter)) {
                    card.classList.add('active');
                    activeCardFound = true;
                } else {
                    card.classList.remove('active');
                }
            });
            const allCard = q('.card[data-filter="all"]');
            if (allCard) {
                if (!activeCardFound) {
                    allCard.classList.add('active');
                } else {
                    allCard.classList.remove('active');
                }
            }
        }

        function bindCopyButtons() {
            qa('.copy-btn').forEach(btn => {
                const sel = btn.getAttribute('data-copy');
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const el = sel ? document.querySelector(sel) : null;
                    if (!el) return;

                    const text = formatTestDetails(el);
                    try {
                        await navigator.clipboard.writeText(text);
                        const prevHtml = btn.innerHTML;
                        btn.innerHTML = '<span>✓</span>';
                        btn.classList.add('copied');
                        setTimeout(() => { btn.classList.remove('copied'); btn.innerHTML = prevHtml; }, 900);
                    } catch (_e) { }
                });
            });
        }

        function formatTestDetails(gridElement) {
            const lines = [];
            const gridItems = qa('.k, .v', gridElement);

            for (let i = 0; i < gridItems.length; i += 2) {
                const key = gridItems[i];
                const value = gridItems[i + 1];

                if (!key || !value) continue;

                const keyText = key.textContent.trim();
                const valueElement = value;

                if (keyText === 'Execution Log') {
                    lines.push(`${keyText}:`);
                    const logText = formatExecutionLog(valueElement);
                    if (logText) {
                        lines.push(logText);
                    }
                } else {
                    const valueText = valueElement.textContent.trim();
                    lines.push(`${keyText}: ${valueText}`);
                }
                lines.push('');
            }

            return lines.join('\n').trim();
        }

        function formatExecutionLog(logContainer) {
            const lines = [];

            function processLogItems(container, indent = '') {
                const items = qa('li', container);
                items.forEach(item => {
                    const parentUl = item.parentElement;
                    if (parentUl && parentUl !== container && parentUl.closest('li') && parentUl.closest('li').parentElement === container) {
                        return;
                    }

                    const text = getDirectTextContent(item).trim();
                    if (text) {
                        lines.push(indent + text);
                    }

                    const nestedUl = qa('ul', item).find(ul => ul.parentElement === item);
                    if (nestedUl) {
                        processLogItems(nestedUl, indent + '  ');
                    }
                });
            }

            function getDirectTextContent(element) {
                let text = '';
                for (const node of element.childNodes) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        text += node.textContent;
                    } else if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.tagName === 'STRONG' || node.tagName === 'CODE' || node.tagName === 'BUTTON') {
                            text += node.textContent;
                        }
                        if (node.tagName !== 'UL') {
                            if (!qa('ul', node).length) {
                                text += node.textContent;
                            }
                        }
                    }
                }
                return text;
            }

            const topLevelUl = qa('ul', logContainer)[0];
            if (topLevelUl) {
                processLogItems(topLevelUl);
            }

            return lines.join('\n');
        }

        function bindModalButtons() {
            qa('[data-modal-target]').forEach(button => {
                button.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const modal = document.querySelector(button.dataset.modalTarget);
                    if (modal) {
                        modal.hidden = false;
                        document.body.style.overflow = 'hidden';
                    }
                });
            });

            qa('[data-modal-close]').forEach(element => {
                element.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const modal = element.closest('.modal');
                    if (modal) {
                        modal.hidden = true;
                        document.body.style.overflow = '';
                    }
                });
            });
        }

        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModal = q('.modal:not([hidden])');
                if (openModal) {
                    openModal.hidden = true;
                    document.body.style.overflow = '';
                }
            }
        });

        function bindAssertToggles() {
            qa('[data-toggle-target]').forEach(element => {
                element.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const targetSelector = element.dataset.toggleTarget;
                    const target = document.querySelector(targetSelector);
                    if (target) {
                        const isHidden = target.style.display === 'none' || !target.style.display;
                        target.style.display = isHidden ? 'block' : 'none';
                    }
                });
                
                element.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        e.stopPropagation();
                        element.click();
                    }
                });
            });
        }

        updateCardStyles();
        bindCopyButtons();
        bindModalButtons();
        bindAssertToggles();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setupTheme();
            init();
        }, { once: true });
    } else {
        setupTheme();
        init();
    }
})();
