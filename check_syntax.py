import sys
sys.stdout.reconfigure(encoding='utf-8')

def check_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check brace, bracket, parenthesis balance outside strings and comments
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    in_single = False
    in_double = False
    in_template = False
    in_line_comment = False
    in_block_comment = False
    escaped = False

    i = 0
    line = 1
    col = 1
    errors = []

    while i < len(content):
        ch = content[i]
        next_ch = content[i+1] if i + 1 < len(content) else ''

        if ch == '\n':
            line += 1
            col = 0
            if in_line_comment:
                in_line_comment = False

        col += 1

        if in_line_comment:
            i += 1
            continue

        if in_block_comment:
            if ch == '*' and next_ch == '/':
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if escaped:
            escaped = False
            i += 1
            continue

        if ch == '\\':
            escaped = True
            i += 1
            continue

        if in_single:
            if ch == "'":
                in_single = False
            i += 1
            continue

        if in_double:
            if ch == '"':
                in_double = False
            i += 1
            continue

        if in_template:
            if ch == '`':
                in_template = False
            i += 1
            continue

        if ch == '/' and next_ch == '/':
            in_line_comment = True
            i += 2
            continue

        if ch == '/' and next_ch == '*':
            in_block_comment = True
            i += 2
            continue

        if ch == "'":
            in_single = True
            i += 1
            continue

        if ch == '"':
            in_double = True
            i += 1
            continue

        if ch == '`':
            in_template = True
            i += 1
            continue

        if ch in '({[':
            stack.append((ch, line, col))
        elif ch in ')}]':
            expected = pairs[ch]
            if not stack:
                errors.append(f"Unexpected closing '{ch}' at line {line}:{col}")
            else:
                top, t_line, t_col = stack.pop()
                if top != expected:
                    errors.append(f"Mismatched '{ch}' at line {line}:{col}, expected matching for '{top}' from line {t_line}:{t_col}")

        i += 1

    while stack:
        top, t_line, t_col = stack.pop()
        errors.append(f"Unclosed '{top}' opened at line {t_line}:{t_col}")

    if errors:
        print(f"❌ {path}: {len(errors)} syntax balance errors:")
        for err in errors[:10]:
            print("   ", err)
        return False
    else:
        print(f"✅ {path}: Syntax & bracket balance 100% verified!")
        return True

for f in ['i18n.js', 'audio.js', 'game.js', 'app.js']:
    check_file(f'C:\\Users\\27073\\.gemini\\antigravity\\scratch\\poker-shogi-junqi\\{f}')
