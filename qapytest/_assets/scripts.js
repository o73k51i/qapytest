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
        const savedTheme = sessionStorage.getItem('report-theme');
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
                sessionStorage.setItem('report-theme', newTheme);
                applyTheme(newTheme);
            });
        }

        try {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
                const saved = sessionStorage.getItem('report-theme');
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
                        btn.innerHTML = '<span>✓</span> Copy';
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
                    // Clone the element to manipulate it without affecting the DOM
                    const clone = valueElement.cloneNode(true);
                    // Remove details-actions (buttons) from the clone
                    const actions = clone.querySelector('.details-actions');
                    if (actions) {
                        actions.remove();
                    }
                    const valueText = clone.textContent.trim();
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

                    let text = '';

                    if (item.classList.contains('step-passed') || item.classList.contains('step-failed')) {
                        const stepIcon = item.classList.contains('step-passed') ? '✔︎' : '✖︎';

                        const strongElement = item.querySelector('strong');
                        if (strongElement && strongElement.nextSibling) {
                            const stepText = strongElement.nextSibling.textContent?.trim() || '';
                            text = `${stepIcon} ${stepText}`;
                        } else {
                            const fullText = item.textContent || '';
                            const cleaned = fullText.replace(/^[✔︎✖︎]\s*Step:\s*/, '').replace(/\s*[✔︎✖︎].*$/, '').trim();
                            const lines = cleaned.split('\n').filter(line => line.trim());
                            text = `${stepIcon} ${lines[0] || ''}`;
                        }
                    }
                    else if (item.classList.contains('assert-passed') || item.classList.contains('assert-failed')) {
                        const assertIcon = item.classList.contains('assert-passed') ? '✔︎' : '✖︎';
                        const assertLabel = item.querySelector('.assert-label');

                        if (assertLabel) {
                            let labelText = '';
                            for (const node of assertLabel.childNodes) {
                                if (node.nodeType === Node.TEXT_NODE) {
                                    labelText += node.textContent;
                                }
                            }
                            labelText = labelText.replace(/^[✔︎✖︎\s]*/, '').trim();
                            text = `${assertIcon} ${labelText}`;

                            const detailsDiv = item.querySelector('.assert-details');
                            if (detailsDiv) {
                                const detailsContent = detailsDiv.querySelector('.details-content');
                                if (detailsContent) {
                                    const detailLines = Array.from(detailsContent.children)
                                        .map(child => child.textContent.trim())
                                        .filter(line => line)
                                        .join(' ');
                                    if (detailLines) {
                                        const maxLength = 150;
                                        const truncatedDetails = detailLines.length > maxLength
                                            ? detailLines.substring(0, maxLength) + '...'
                                            : detailLines;
                                        text += ` (${truncatedDetails})`;
                                    }
                                }
                            }
                        }
                    }

                    if (text) {
                        const maxIndentLevel = 3;
                        const currentIndentLevel = indent.length / 2;
                        const actualIndent = currentIndentLevel <= maxIndentLevel ? indent : '      ';
                        lines.push(actualIndent + text);
                    }

                    const nestedUl = qa('ul', item).find(ul => ul.parentElement === item);
                    if (nestedUl) {
                        const nextIndent = indent.length < 6 ? indent + '  ' : indent;
                        processLogItems(nestedUl, nextIndent);
                    }
                });
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

                        const modalBody = modal.querySelector('.modal-body');
                        const preElement = modalBody.querySelector('pre code');
                        if (preElement && modal.id.includes('logs-modal')) {
                            formatLogsAsTable(preElement);
                        }
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

        function formatLogsAsTable(codeElement) {
            const logText = codeElement.textContent;
            const lines = logText.split('\n');
            const modal = codeElement.closest('.modal');
            
            const filterWrapper = modal ? modal.querySelector('.log-filter-wrapper') : null;
            const filterToggle = modal ? modal.querySelector('.log-filter-toggle') : null;
            const filterMenu = modal ? modal.querySelector('.log-filter-menu') : null;
            const filterList = modal ? modal.querySelector('.log-filter-list') : null;
            const allCheckbox = modal ? modal.querySelector('input[value="all"]') : null;
            const copyBtn = modal ? modal.querySelector('.log-copy-btn') : null;
            
            const loggers = new Set();

            if (lines.length === 0) return;

            const table = document.createElement('table');
            table.className = 'logs-table';

            let i = 0;
            while (i < lines.length) {
                const line = lines[i].trim();
                if (!line) {
                    i++;
                    continue;
                }

                const row = document.createElement('tr');

                const logMatch = line.match(/^(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\s+(.+?):(.+?):(\d+)\s+(.*)$/i);

                if (logMatch) {
                    const [, level, logger, file, lineNum, message] = logMatch;
                    loggers.add(logger);
                    row.dataset.logger = logger;

                    let fullMessage = message;
                    let j = i + 1;
                    while (j < lines.length) {
                        const nextLine = lines[j].trim();
                        if (!nextLine) {
                            j++;
                            continue;
                        }

                        const nextLogMatch = nextLine.match(/^(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\s+/i);
                        if (nextLogMatch) {
                            break;
                        }

                        fullMessage += '\n' + lines[j];
                        j++;
                    }

                    const levelCell = document.createElement('td');
                    levelCell.className = `log-level ${level.toUpperCase()}`;
                    levelCell.textContent = level.toUpperCase();
                    row.appendChild(levelCell);

                    const loggerCell = document.createElement('td');
                    loggerCell.className = 'log-logger';
                    loggerCell.textContent = logger;
                    loggerCell.title = `${logger}:${file}:${lineNum}`;
                    row.appendChild(loggerCell);

                    const messageCell = document.createElement('td');
                    messageCell.className = 'log-message';

                    if (fullMessage.includes('\n')) {
                        messageCell.style.whiteSpace = 'pre-wrap';
                        messageCell.style.fontFamily = 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace';
                    }

                    messageCell.textContent = fullMessage;
                    row.appendChild(messageCell);

                    i = j;
                } else {
                    const simpleMatch = line.match(/^(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\s+(.*)$/i);

                    if (simpleMatch) {
                        const [, level, rest] = simpleMatch;

                        const levelCell = document.createElement('td');
                        levelCell.className = `log-level ${level.toUpperCase()}`;
                        levelCell.textContent = level.toUpperCase();
                        row.appendChild(levelCell);

                        const loggerCell = document.createElement('td');
                        loggerCell.className = 'log-logger';
                        loggerCell.textContent = '';
                        row.appendChild(loggerCell);

                        const messageCell = document.createElement('td');
                        messageCell.className = 'log-message';
                        messageCell.textContent = rest;
                        row.appendChild(messageCell);

                        i++;
                    } else {
                        i++;
                        continue;
                    }
                }

                table.appendChild(row);
            }

            if (filterList && loggers.size > 0) {
                filterList.innerHTML = '';
                const sortedLoggers = Array.from(loggers).sort();
                
                sortedLoggers.forEach(logger => {
                    const label = document.createElement('label');
                    label.className = 'log-filter-item';
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.value = logger;
                    checkbox.checked = true;
                    
                    const span = document.createElement('span');
                    span.textContent = logger;
                    
                    label.appendChild(checkbox);
                    label.appendChild(span);
                    filterList.appendChild(label);
                    
                    checkbox.addEventListener('change', () => {
                        updateVisibility();
                        updateAllCheckboxState();
                    });
                });

                if (allCheckbox) {
                    allCheckbox.checked = true;
                    allCheckbox.addEventListener('change', (e) => {
                        const checked = e.target.checked;
                        const checkboxes = filterList.querySelectorAll('input[type="checkbox"]');
                        checkboxes.forEach(cb => cb.checked = checked);
                        updateVisibility();
                    });
                }

                function updateAllCheckboxState() {
                    if (!allCheckbox) return;
                    const checkboxes = Array.from(filterList.querySelectorAll('input[type="checkbox"]'));
                    const allChecked = checkboxes.every(cb => cb.checked);
                    const someChecked = checkboxes.some(cb => cb.checked);
                    allCheckbox.checked = allChecked;
                    allCheckbox.indeterminate = someChecked && !allChecked;
                }

                function updateVisibility() {
                    const checkboxes = Array.from(filterList.querySelectorAll('input[type="checkbox"]'));
                    const checkedLoggers = new Set(checkboxes.filter(cb => cb.checked).map(cb => cb.value));
                    
                    const rows = table.querySelectorAll('tr');
                    rows.forEach(row => {
                        const logger = row.dataset.logger;
                        if (logger) {
                            row.style.display = checkedLoggers.has(logger) ? '' : 'none';
                        } else {
                            row.style.display = ''; 
                        }
                    });
                }
                
                if (filterToggle) {
                    filterToggle.addEventListener('click', (e) => {
                        e.stopPropagation();
                        filterMenu.hidden = !filterMenu.hidden;
                    });
                }
            } else if (filterWrapper) {
                // Hide filter if no loggers found
                filterWrapper.style.display = 'none';
            }

            if (copyBtn) {
                copyBtn.addEventListener('click', async () => {
                    try {
                        const visibleRows = Array.from(table.querySelectorAll('tr')).filter(row => row.style.display !== 'none');
                        const textParts = visibleRows.map(row => {
                            const logger = row.dataset.logger;
                            const message = row.querySelector('.log-message')?.textContent || '';
                            
                            if (logger) {
                                return `${logger}: ${message}`;
                            }
                            return message;
                        });
                        
                        const textToCopy = textParts.join('\n');
                        
                        await navigator.clipboard.writeText(textToCopy);
                        const prevHtml = copyBtn.innerHTML;
                        copyBtn.innerHTML = '<span>✓</span> Copy';
                        copyBtn.classList.add('copied');
                        setTimeout(() => {
                            copyBtn.classList.remove('copied');
                            copyBtn.innerHTML = prevHtml;
                        }, 900);
                    } catch (_e) { }
                });
            }

            const preElement = codeElement.parentElement;
            preElement.parentElement.replaceChild(table, preElement);
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

        document.addEventListener('click', (e) => {
            const menus = qa('.log-filter-menu:not([hidden])');
            menus.forEach(menu => {
                const wrapper = menu.closest('.log-filter-wrapper');
                if (wrapper && !wrapper.contains(e.target)) {
                    menu.hidden = true;
                }
            });
        });

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
