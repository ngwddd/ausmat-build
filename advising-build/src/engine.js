
/* ============================================================================
 * The engine.
 *
 * This file contains NO advice text. It reads the catalog, evaluates each
 * rule's `when` expression against the student record through a validating
 * evaluator, and assembles the report. Editing advice never means editing here.
 * ==========================================================================*/
(function () {
  'use strict'

  var R = window.ADVISING

  /* ---------------------------------------------------------------------
   * A small, self-contained expression evaluator — no new Function, no eval.
   *
   * Why not compile the rule expressions with Function(): doing so exposes the
   * whole global scope to the expression. `record.constructor.constructor(...)`
   * and a bare `globalThis` are both reachable, and neither can be excluded by
   * scanning the text, because the escape happens through the language runtime
   * rather than through a name the scanner can see. Wrapping the scope in a
   * Proxy narrows it but cannot close it, since a `with` block's scope chain
   * still terminates at the global object.
   *
   * Parsing the expression and evaluating the tree removes the problem instead
   * of mitigating it: there is no global scope to reach, `this` and `new` are
   * not part of the grammar, and a mistyped helper is a plain error naming the
   * rule. The catalog stays data, and the engine stays in charge.
   * -------------------------------------------------------------------*/
  var OPERATORS = [
    '===', '!==', '==', '!=', '<=', '>=', '&&', '||',
    '<', '>', '+', '-', '*', '/', '%', '!', '(', ')', '[', ']', '.', ',', '?', ':',
  ]

  function tokenize(input) {
    var tokens = []
    var i = 0
    while (i < input.length) {
      var ch = input[i]
      if (/\s/.test(ch)) { i++; continue }
      if (ch === '"' || ch === "'") {
        var quote = ch
        var value = ''
        i++
        while (i < input.length && input[i] !== quote) {
          if (input[i] === '\\') { value += input[i + 1]; i += 2; continue }
          value += input[i++]
        }
        if (input[i] !== quote) throw new Error('unterminated string literal')
        i++
        tokens.push({ type: 'string', value: value })
        continue
      }
      if (/[0-9]/.test(ch)) {
        var num = ''
        while (i < input.length && /[0-9.]/.test(input[i])) num += input[i++]
        tokens.push({ type: 'number', value: Number(num) })
        continue
      }
      if (/[A-Za-z_$]/.test(ch)) {
        var name = ''
        while (i < input.length && /[A-Za-z0-9_$]/.test(input[i])) name += input[i++]
        tokens.push({ type: 'name', value: name })
        continue
      }
      var matched = null
      for (var o = 0; o < OPERATORS.length; o++) {
        if (input.substr(i, OPERATORS[o].length) === OPERATORS[o]) { matched = OPERATORS[o]; break }
      }
      if (!matched) throw new Error('unexpected character "' + ch + '"')
      tokens.push({ type: 'op', value: matched })
      i += matched.length
    }
    tokens.push({ type: 'eof', value: '' })
    return tokens
  }

  function parseExpression(source) {
    var tokens = tokenize(source)
    var pos = 0
    function peek() { return tokens[pos] }
    function eat(value) {
      var t = tokens[pos]
      if (t.type === 'op' && t.value === value) { pos++; return true }
      return false
    }
    function expect(value) {
      if (!eat(value)) throw new Error('expected "' + value + '"')
    }
    function parsePrimary() {
      var t = peek()
      if (t.type === 'number') { pos++; return { kind: 'literal', value: t.value } }
      if (t.type === 'string') { pos++; return { kind: 'literal', value: t.value } }
      if (t.type === 'name') {
        pos++
        if (t.value === 'true') return { kind: 'literal', value: true }
        if (t.value === 'false') return { kind: 'literal', value: false }
        if (t.value === 'null') return { kind: 'literal', value: null }
        return { kind: 'name', name: t.value }
      }
      if (eat('[')) {
        // Array literal, used to compare one path against several values:
        // anyInterest('i.country', ['Australia', 'United Kingdom'])
        var items = []
        if (!eat(']')) {
          do { items.push(parseTernary()) } while (eat(','))
          expect(']')
        }
        // Elements must be constants. Evaluating with an empty scope makes any
        // reference to a record field a parse-time error rather than a value
        // silently captured before the student's data exists.
        return { kind: 'literal', value: items.map(constantOf) }
      }
      if (eat('(')) { var inner = parseTernary(); expect(')'); return inner }
      throw new Error('unexpected token "' + t.value + '"')
    }
    function parsePostfix() {
      var node = parsePrimary()
      for (;;) {
        if (eat('.')) {
          var prop = peek()
          if (prop.type !== 'name') throw new Error('expected a property name after "."')
          pos++
          node = { kind: 'member', object: node, property: prop.value }
          continue
        }
        if (peek().type === 'op' && peek().value === '[') {
          pos++
          var index = parseTernary()
          expect(']')
          node = { kind: 'computed', object: node, index: index }
          continue
        }
        if (peek().type === 'op' && peek().value === '(') {
          pos++
          var args = []
          if (!eat(')')) {
            do { args.push(parseTernary()) } while (eat(','))
            expect(')')
          }
          node = { kind: 'call', callee: node, args: args }
          continue
        }
        return node
      }
    }
    function parseUnary() {
      if (eat('!')) return { kind: 'unary', op: '!', argument: parseUnary() }
      if (eat('-')) return { kind: 'unary', op: '-', argument: parseUnary() }
      return parsePostfix()
    }
    function binaryLevel(ops, next) {
      return function () {
        var node = next()
        for (;;) {
          var t = peek()
          if (t.type !== 'op' || ops.indexOf(t.value) === -1) return node
          pos++
          node = { kind: 'binary', op: t.value, left: node, right: next() }
        }
      }
    }
    var parseMul = binaryLevel(['*', '/', '%'], parseUnary)
    var parseAdd = binaryLevel(['+', '-'], parseMul)
    var parseRel = binaryLevel(['<', '>', '<=', '>='], parseAdd)
    var parseEq = binaryLevel(['==', '!=', '===', '!=='], parseRel)
    var parseAnd = binaryLevel(['&&'], parseEq)
    var parseOr = binaryLevel(['||'], parseAnd)
    function parseTernary() {
      var node = parseOr()
      if (eat('?')) {
        var consequent = parseTernary()
        expect(':')
        var alternate = parseTernary()
        return { kind: 'conditional', test: node, consequent: consequent, alternate: alternate }
      }
      return node
    }
    var ast = parseTernary()
    if (peek().type !== 'eof') {
      throw new Error('unexpected trailing token "' + peek().value + '"')
    }
    return ast
  }

  // Only these object methods may be called from a rule. An expression cannot
  // reach a method that is not on this list, so a callback cannot be handed to
  // something that would run it outside the evaluator.
  var METHOD_ALLOWLIST = ['some', 'every', 'includes', 'indexOf', 'test', 'match', 'startsWith', 'endsWith']

  // Property names that must never resolve, on any value, by any access form.
  // Comments in this template use the word "constructor" several times, but the
  // real blocking is deliberately structural: the obvious form
  // `record.constructor.constructor(...)()` is blocked by the call rule, yet
  // `record["constructor"]` still reaches the Function constructor, and that is
  // both a real reflective escape and, in a rule, always a typo.
  var DENIED_PROPERTIES = ['constructor', '__proto__', 'prototype', 'caller', 'callee', 'arguments']

  function readProperty(target, key) {
    if (typeof key === 'string' && DENIED_PROPERTIES.indexOf(key) !== -1) {
      throw new Error('property "' + key + '" is not available to a rule')
    }
    return target[key]
  }

  // Only constant sub-expressions may appear inside an array literal.
  function constantOf(node) {
    if (node.kind === 'literal') return node.value
    throw new Error('array literal elements must be constants')
  }

  function evaluateAst(node, scope) {
    switch (node.kind) {
      case 'literal':
        return node.value
      case 'name':
        if (Object.prototype.hasOwnProperty.call(scope, node.name)) return scope[node.name]
        throw new Error('unknown name "' + node.name + '"')
      case 'member': {
        var target = evaluateAst(node.object, scope)
        if (target === null || target === undefined) return undefined
        return readProperty(target, node.property)
      }
      case 'computed': {
        var owner = evaluateAst(node.object, scope)
        if (owner === null || owner === undefined) return undefined
        return readProperty(owner, evaluateAst(node.index, scope))
      }
      case 'call': {
        if (node.callee.kind === 'name') {
          var helper = scope[node.callee.name]
          if (typeof helper !== 'function') throw new Error('"' + node.callee.name + '" is not a helper function')
          // Helper arguments are passed UNEVALUATED. A helper such as
          // anyInterest binds `i` per element, so the path argument must not be
          // resolved against the outer scope, where `i` does not exist yet.
          return helper.apply(null, [scope, node.args])
        }
        var receiver = evaluateAst(node.callee.object, scope)
        var method = node.callee.property
        if (METHOD_ALLOWLIST.indexOf(method) === -1) {
          throw new Error('method "' + method + '" is not permitted in a rule')
        }
        var fn = receiver[method]
        if (typeof fn !== 'function') throw new Error('"' + method + '" is not callable here')
        return fn.apply(receiver, node.args.map(function (a) { return evaluateAst(a, scope) }))
      }
      case 'unary':
        return node.op === '!' ? !evaluateAst(node.argument, scope) : -evaluateAst(node.argument, scope)
      case 'binary': {
        // Short-circuit rather than evaluating both sides.
        if (node.op === '&&') return evaluateAst(node.left, scope) ? evaluateAst(node.right, scope) : false
        if (node.op === '||') { var l = evaluateAst(node.left, scope); return l ? l : evaluateAst(node.right, scope) }
        var a = evaluateAst(node.left, scope)
        var b = evaluateAst(node.right, scope)
        switch (node.op) {
          case '+': return a + b
          case '-': return a - b
          case '*': return a * b
          case '/': return a / b
          case '%': return a % b
          case '==': return a == b // eslint-disable-line eqeqeq
          case '!=': return a != b // eslint-disable-line eqeqeq
          case '===': return a === b
          case '!==': return a !== b
          case '<': return a < b
          case '>': return a > b
          case '<=': return a <= b
          case '>=': return a >= b
        }
        throw new Error('unsupported operator "' + node.op + '"')
      }
      case 'conditional':
        return evaluateAst(node.test, scope) ? evaluateAst(node.consequent, scope) : evaluateAst(node.alternate, scope)
    }
    throw new Error('unsupported expression form "' + node.kind + '"')
  }

  var compiled = {}
  var compileErrors = {}
  R.rules.forEach(function (rule) {
    try {
      var ast = parseExpression(rule.when)
      compiled[rule.id] = function (record, helpers) {
        return evaluateAst(ast, Object.assign({ record: record, T: R.thresholds }, helpers))
      }
    } catch (error) {
      compileErrors[rule.id] = error.message
    }
  })

  /* -------------------------- helpers the rules may use ---------------
   * Comparisons against list elements take a field expression plus an optional
   * expected value. The rule language has no function syntax, so anyInterest
   * contains the traversal: the rule names the field, the engine binds `i`.
   * -------------------------------------------------------------------*/
  function resolvePath(start, path) {
    return String(path).split('.').reduce(function (value, key) {
      return value === null || value === undefined ? undefined : value[key]
    }, start)
  }

  function pathMatches(pathValue, expected) {
    if (expected === undefined) return !!pathValue
    if (Array.isArray(expected)) return expected.indexOf(pathValue) !== -1
    return pathValue === expected
  }

  // Capability lookup: the catalog owns the mapping from a capability key to the
  // subject names that satisfy it, so a rule asks "does this student have the
  // mathematics a course expects" without enumerating subject names itself.
  function hasCapability(subjects, key) {
    var cap = R.capabilities && R.capabilities[key]
    if (!cap) return false
    return (subjects || []).some(function (s) {
      return cap.subjects.indexOf(s.subject) !== -1
    })
  }

  function expectationFor(field) {
    return (R.courseExpectations && R.courseExpectations[field]) || null
  }

  // Helper contract for every anyInterest* helper: the FIRST argument is a path
  // string resolved per element, so the helper can reach a field on the element;
  // every remaining argument is evaluated once in the caller's scope. One rule
  // for all of them, because a mixed convention is how a condition ends up
  // calling a helper with the wrong kind of argument.
  function buildHelpers(record, scope) {
    return {
      anyInterest: function (currentScope, args) {
        if (args.length === 0) {
          throw new Error('anyInterest needs a field path, e.g. anyInterest("i.country", "Australia")')
        }
        var path = evaluateAst(args[0], currentScope)
        var expected = args.length > 1 ? evaluateAst(args[1], currentScope) : undefined
        return record.interests.some(function (interest) {
          var elementScope = Object.assign({}, currentScope, { i: interest, item: interest })
          return pathMatches(resolvePath(elementScope, path), expected)
        })
      },
      // Explicit "this field is absent" predicate. anyInterest(path, null) would
      // NOT mean this: a null second argument is indistinguishable from an
      // omitted one, where the comparison falls back to truthiness. Naming the
      // intent avoids a trap the language cannot express clearly.
      // anyInterestMissing was here: it reported any interest whose named field
      // was blank. The only field it was ever pointed at was the per-interest
      // minimum ATAR, which no control set — so it was true for every record with
      // a choice, and the rule built on it fired on every report. anyInterestUnmatched
      // asks the question that still has an answer: does the library know this choice?
      // fieldPath -> a capability field the stated course expectation requires.
      anyInterestExpectationGap: function (currentScope, args) {
        if (args.length < 2) {
          throw new Error('anyInterestExpectationGap needs a field path and the subjects, e.g. anyInterestExpectationGap("i.field", record.subjects)')
        }
        var path = evaluateAst(args[0], currentScope)
        var subjects = evaluateAst(args[1], currentScope)
        return record.interests.some(function (interest) {
          var field = resolvePath({ i: interest, item: interest }, path)
          var expectation = expectationFor(field)
          if (!expectation) return false
          return expectation.expects.some(function (key) { return !hasCapability(subjects, key) })
        })
      },
      // fieldPath -> an optional capability that would strengthen the case. Only
      // reported once the required set is covered, so it never competes with the
      // prerequisite-gap message for the same field.
      anyInterestOptionalGap: function (currentScope, args) {
        if (args.length < 2) {
          throw new Error('anyInterestOptionalGap needs a field path and the subjects, e.g. anyInterestOptionalGap("i.field", record.subjects)')
        }
        var path = evaluateAst(args[0], currentScope)
        var subjects = evaluateAst(args[1], currentScope)
        return record.interests.some(function (interest) {
          var field = resolvePath({ i: interest, item: interest }, path)
          var expectation = expectationFor(field)
          if (!expectation || !expectation.optional.length) return false
          if (expectation.expects.some(function (key) { return !hasCapability(subjects, key) })) return false
          return expectation.optional.some(function (key) { return !hasCapability(subjects, key) })
        })
      },
      // belowStatedMinimum was here: it compared a standing against a per-interest
      // minimum. That field is gone — it was always null, no control ever set it —
      // so the helper had no caller left, and a helper the rules cannot use is
      // documentation for something that does not exist. The near-miss case it
      // covered is now nearestAboveWithin, which reads the course library.
      countSubject: function (currentScope, args) {
        // Counts recorded subjects whose NAME starts with the prefix. It used to
        // test `s.level`, which could never match: the prefix rules pass is "AT"
        // — the marker the source workbook puts on ATAR subjects (ATMAM, ATPHY,
        // …) — and the level dropdown held intake names instead. So the one rule
        // that calls this was unreachable by construction. With the subject
        // pick-list still to come, the field name is now the right one, and
        // perf-high-at-load stays switched off until a student can actually
        // choose an AT code rather than type a course name.
        var prefix = evaluateAst(args[0], currentScope)
        return record.subjects.filter(function (s) {
          return s.subject && s.subject.indexOf(prefix) === 0
        }).length
      },
      anyScoreBelow: function (currentScope, args) {
        var n = evaluateAst(args[0], currentScope)
        return record.subjects.some(function (s) {
          return typeof s.mark === 'number' && s.mark < n
        })
      },
      anyValueBelow: function (currentScope, args) {
        var container = evaluateAst(args[0], currentScope)
        var n = evaluateAst(args[1], currentScope)
        if (!container || typeof container !== 'object') return false
        return Object.keys(container).some(function (k) {
          return typeof container[k] === 'number' && container[k] < n
        })
      },
      hasSubject: function (currentScope, args) {
        var name = evaluateAst(args[0], currentScope)
        return record.subjects.some(function (s) { return s.subject === name })
      },
      score: function (currentScope, args) {
        var subject = evaluateAst(args[0], currentScope)
        var hit = record.subjects.filter(function (s) { return s.subject === subject })[0]
        return hit && typeof hit.mark === 'number' ? hit.mark : null
      },
    }
  }

  /* -------------------------- token interpolation ---------------------
   * Thresholds are interpolated from the catalog, not the record, so advice
   * text can state the same figure its condition tests. That is what keeps
   * "below 60" in the prose and `anyScoreBelow(T.weakMark)` in the condition
   * from drifting apart.
   * -------------------------------------------------------------------*/
  function interpolate(text, record) {
    return String(text).replace(/\{\{(\w+)\}\}/g, function (whole, key) {
      if (key === 'subjectCount') return String(record.subjects.length)
      if (Object.prototype.hasOwnProperty.call(R.thresholds, key)) return String(R.thresholds[key])
      var value = record[key]
      return value === undefined || value === null || value === '' ? '—' : String(value)
    })
  }

  /* -------------------------- DOM plumbing ---------------------------- */
  function $(id) { return document.getElementById(id) }
  function el(tag, attrs, kids) {
    var node = document.createElement(tag)
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === 'text') node.textContent = attrs[k]
      else if (k === 'html') node.innerHTML = attrs[k]
      else if (k.indexOf('on') === 0) node.addEventListener(k.slice(2), attrs[k])
      else node.setAttribute(k, attrs[k])
    })
    ;(kids || []).forEach(function (kid) { node.appendChild(kid) })
    return node
  }
  function options(list, selected, blankLabel) {
    var frag = document.createDocumentFragment()
    if (blankLabel !== undefined) {
      var b = el('option', { value: '' }, [])
      b.textContent = blankLabel
      frag.appendChild(b)
    }
    list.forEach(function (value) {
      var o = el('option', { value: value }, [])
      o.textContent = value
      if (value === selected) o.selected = true
      frag.appendChild(o)
    })
    return frag
  }

  /* ---------------------------------------------------------------------
   * Record construction. A blank mark is null, never 0 — conflating "not yet
   * assessed" with "scored zero" is a data-modelling error that changes what
   * the advice says.
   * -------------------------------------------------------------------*/
  function numOrNull(v) {
    if (v === '' || v === null || v === undefined) return null
    var n = Number(v)
    return isNaN(n) ? null : n
  }
  function boolOrNull(v) {
    if (v === '') return null
    return v === 'true'
  }
  function parsePairs(text) {
    var out = {}
    String(text || '').split('\n').forEach(function (line) {
      var m = /^\s*([^:]+):\s*(-?[\d.]+)\s*$/.exec(line)
      if (m) out[m[1].trim()] = Number(m[2])
    })
    return out
  }

  function readRecord() {
    var interests = []
    Array.prototype.forEach.call($('interestRows').querySelectorAll('tr'), function (tr) {
      var country = tr.querySelector('.i-country').value
      var field = tr.querySelector('.i-field').value
      var uni = tr.querySelector('.i-uni').value
      if (country || field || uni) {
        // No atarRequirement: the field was always null, because no control ever
        // set it, and a rule read it as "the student has not recorded a figure"
        // — so it fired on every report with a choice and told the reader to
        // record something the form could not collect. The minimum now comes
        // from the course library, matched on all three of these values, which
        // is why the institution is a pick-list rather than a text box.
        interests.push({ country: country, field: field, university: uni })
      }
    })
    var subjects = []
    Array.prototype.forEach.call($('subjectRows').querySelectorAll('tr'), function (tr) {
      var subject = tr.querySelector('.s-subject').value.trim()
      var mark = numOrNull(tr.querySelector('.s-mark').value)
      if (subject) {
        subjects.push({ subject: subject, mark: mark })
      }
    })
    var rec = {
      fullName: $('fullName').value.trim(),
      studentId: $('studentId').value.trim(),
      year11School: $('year11School').value.trim(),
      englishFirstLanguage: boolOrNull($('englishFirstLanguage').value),
      previousIntake: $('previousIntake').value || null,
      targetAtar: numOrNull($('targetAtar').value),
      stillDeciding: $('stillDeciding').value === 'true',
      fundingSecured: boolOrNull($('fundingSecured').value),
      interests: interests,
      subjects: subjects,
      year11: parsePairs($('year11Results').value),
      priorResults: parsePairs($('priorResults').value),
    }
    // The standing is COMPUTED, not asked for. It used to be a typed estimate
    // ("Current (estimated) ATAR"), and the entire course-library comparison was
    // gated on it: atarComparison returns null without a standing, so
    // anyInterestHasCourses was false, so every rule that compares the student
    // against a recorded minimum stayed silent unless the student first guessed
    // a number. The tool can work this out from the marks it already has.
    // Null when the marks cannot be converted, which keeps those rules silent
    // rather than comparing against a figure that does not exist.
    rec.computedAtar = atarPicture(rec).atar
    return rec
  }

  function writeRecord(rec) {
    $('fullName').value = rec.fullName || ''
    $('studentId').value = rec.studentId || ''
    $('year11School').value = rec.year11School || ''
    $('englishFirstLanguage').value = rec.englishFirstLanguage === null || rec.englishFirstLanguage === undefined ? '' : String(rec.englishFirstLanguage)
    $('previousIntake').value = rec.previousIntake || ''
    $('targetAtar').value = rec.targetAtar === null || rec.targetAtar === undefined ? '' : rec.targetAtar
    $('stillDeciding').value = rec.stillDeciding ? 'true' : 'false'
    $('fundingSecured').value = rec.fundingSecured === null || rec.fundingSecured === undefined ? '' : String(rec.fundingSecured)
    $('year11Results').value = Object.keys(rec.year11 || {}).map(function (k) { return k + ': ' + rec.year11[k] }).join('\n')
    $('priorResults').value = Object.keys(rec.priorResults || {}).map(function (k) { return k + ': ' + rec.priorResults[k] }).join('\n')

    $('interestRows').innerHTML = ''
    ;(rec.interests && rec.interests.length ? rec.interests : [{}]).forEach(addInterestRow)
    $('subjectRows').innerHTML = ''
    ;(rec.subjects && rec.subjects.length ? rec.subjects : [{}]).forEach(addSubjectRow)
  }

  /* An interest row: where, what field, and which institution.
   *
   * The last cell reports what the library holds for the combination. Three
   * things here are deliberate, because the first version was not rigorous:
   *
   *   1. The institution list depends on the country. Offering all sixteen under
   *      every country let a student record "Australia + Sunway University",
   *      which can never match anything, and the only feedback was a dash.
   *   2. The cell reports a RANGE and a COUNT, not one number. A single figure
   *      was the lowest matching course, which silently answered "the easiest
   *      thing there" to a question about the course the student has in mind:
   *      Deakin holds six matching courses from 52.4 to 87.5, and "52.4" is the
   *      floor, not the requirement.
   *   3. When the library holds nothing, the cell says so in words. A dash is
   *      what an unfilled cell looks like, and the two mean opposite things.
   */
  function universitiesIn(country) {
    var seen = {}
    var out = []
    ;(LIBRARY.rows || []).forEach(function (c) {
      var name = String(c.university || '')
      if (!name || seen[name]) return
      if (country && !countryMatches(c.country, country)) return
      seen[name] = true
      out.push(name)
    })
    return out.sort()
  }

  function countriesInLibrary() {
    var seen = {}
    var out = []
    ;(LIBRARY.rows || []).forEach(function (c) {
      if (c.country && !seen[c.country]) { seen[c.country] = true; out.push(c.country) }
    })
    return out.sort()
  }

  function countryInLibrary(country) {
    if (!country) return true
    return (LIBRARY.rows || []).some(function (c) { return countryMatches(c.country, country) })
  }

  function coursesFor(country, field, university) {
    return matchingCourses({ interests: [{ country: country, field: field, university: university }] })
      .slice()
      .sort(function (a, b) { return a.atar - b.atar })
  }

  /* Which of the three values is the one that excludes everything. "No course for
   * that combination" is true and useless: the student needs to know whether to
   * change the country, the institution or the field, and the three have
   * different fixes. The order is deliberate — country first, because it is the
   * coarsest constraint, then the institution, then the field. */
  function libraryDiagnosis(country, field, university) {
    if (!country && !field && !university) return 'blank'
    if (country && !countryInLibrary(country)) return 'country'
    if (university) {
      var here = (LIBRARY.rows || []).filter(function (c) {
        return countryMatches(c.country, country) && String(c.university) === String(university)
      })
      if (!here.length) return 'university'
      return 'field'
    }
    return 'field'
  }

  function addInterestRow(preset) {
    preset = preset || {}
    var tr = el('tr')
    var country = el('select', { 'class': 'i-country', 'aria-label': pick('Country/region', '国家/地区') }, [])
    country.appendChild(options(R.vocabularies.countries, preset.country, pick('— country —', '— 国家/地区 —')))
    var field = el('select', { 'class': 'i-field', 'aria-label': pick('Field of study', '专业方向') }, [])
    field.appendChild(options(R.vocabularies.fields, preset.field, pick('— field —', '— 专业方向 —')))
    var uni = el('select', { 'class': 'i-uni', 'aria-label': pick('Institution', '院校') }, [])
    var recorded = el('td', { 'class': 'muted num' })
    var bin = el('button', {
      'class': 'ghost mini', text: '×',
      'aria-label': pick('Remove this row', '删除这一行'),
      title: pick('Remove this row', '删除这一行'),
    })
    bin.addEventListener('click', function () { tr.remove() })

    // Rebuilt on every country change, keeping the current pick only while the
    // library still offers it there.
    function fillUniversities() {
      var keep = uni.value
      var names = universitiesIn(country.value)
      uni.innerHTML = ''
      uni.appendChild(options(names, names.indexOf(keep) === -1 ? '' : keep, names.length
        ? '— ' + (LANG === 'zh' ? '院校' : 'institution') + ' —'
        : (LANG === 'zh' ? '这个国家课程库里没有院校' : 'no institution for this country')))
    }

    function describeCourses(courses) {
      return courses.slice(0, 10).map(function (c) {
        return c.course + ' (' + c.atar + ')' + (c.category ? ' [' + c.category + ']' : '')
      }).join('\n') + (courses.length > 10 ? '\n…' : '')
    }

    function refresh() {
      var courses = coursesFor(country.value, field.value, uni.value)
      var lo = null
      var hi = null
      courses.forEach(function (c) {
        if (typeof c.atar !== 'number') return
        if (lo === null || c.atar < lo) lo = c.atar
        if (hi === null || c.atar > hi) hi = c.atar
      })
      var d = R.calibration.display.atar
      if (!courses.length) {
        var why = libraryDiagnosis(country.value, field.value, uni.value)
        recorded.textContent = LANG === 'zh' ? '库里没有' : 'not recorded'
        recorded.title = why === 'country'
          ? (LANG === 'zh'
              ? '课程库只覆盖这些国家：' + countriesInLibrary().join('、')
              : 'the library covers only: ' + countriesInLibrary().join(', '))
          : why === 'university'
            ? (LANG === 'zh'
                ? '课程库里没有这所院校在这个国家的记录' + (uni.value ? '（' + uni.value + '）' : '')
                : 'the library records nothing for that institution in that country')
            : (LANG === 'zh'
                ? '这个国家与院校下，没有匹配「' + (field.value || '—') + '」方向的课程'
                : 'no course matching that field for this country and institution')
      } else {
        recorded.textContent = (lo === hi ? lo.toFixed(d) : lo.toFixed(d) + '–' + hi.toFixed(d)) + ' · ' + courses.length
        recorded.title = describeCourses(courses)
      }
    }

    country.addEventListener('change', function () { fillUniversities(); refresh() })
    field.addEventListener('change', refresh)
    uni.addEventListener('change', refresh)

    tr.appendChild(el('td', {}, [country]))
    tr.appendChild(el('td', {}, [field]))
    tr.appendChild(el('td', {}, [uni]))
    tr.appendChild(recorded)
    tr.appendChild(el('td', {}, [bin]))
    $('interestRows').appendChild(tr)
    fillUniversities()
    if (preset.university) uni.value = preset.university
    refresh()
  }

  /* A subject row is a subject and a mark.
   *
   * The subject is a pick-list of the ATAR subject codes, straight from the
   * workbook's own list, because a free-text box could not be matched against
   * anything: the capability layer compares exact strings, so a student who typed
   * "Maths" or "数学" satisfied no prerequisite and the prerequisite rules went
   * quiet without saying why. It also makes the ATAR arithmetic honest — the
   * best-four aggregate is summed from whatever is recorded, and a General
   * subject (whose mark does not count toward an ATAR) is no longer typeable.
   *
   * The row used to carry two more columns, a "level" and an "assessed %", both
   * removed with the reasons recorded in the catalog: the level dropdown held
   * intake names the workbook only ever uses at student level, and the assessed
   * figure was the workbook's "Total (%) already assessed by school", whose
   * calculation was never ported. A column nothing reads is a question with no
   * consequence. */
  function addSubjectRow(preset) {
    preset = preset || {}
    var tr = el('tr')
    var subject = el('select', { 'class': 's-subject', 'aria-label': pick('Subject', '科目') }, [])
    subject.appendChild(options(R.vocabularies.subjects, preset.subject, '— ' + (LANG === 'zh' ? '科目' : 'subject') + ' —'))
    var mark = el('input', {
      'class': 's-mark', type: 'number', min: '0', max: '100',
      'aria-label': pick('Mark (%)', '成绩 (%)'),
    })
    mark.value = preset.mark === null || preset.mark === undefined ? '' : preset.mark
    // The visible text is a multiplication sign; without a name a screen reader
    // announces only "button", which says nothing about what gets removed.
    var bin = el('button', {
      'class': 'ghost mini', text: '×',
      'aria-label': pick('Remove this subject', '删除这门科目'),
      title: pick('Remove this subject', '删除这门科目'),
    })
    bin.addEventListener('click', function () { tr.remove() })
    tr.appendChild(el('td', {}, [subject]))
    tr.appendChild(el('td', {}, [mark]))
    tr.appendChild(el('td', {}, [bin]))
    $('subjectRows').appendChild(tr)
  }

  /* ---------------------------------------------------------------------
   * Validation. Returns problems, each naming the field and the reason.
   * The engine refuses to generate a report while any error stands, rather
   * than emitting advice computed from bad input.
   * -------------------------------------------------------------------*/
  function validate(rec) {
    var errors = []
    var warnings = []
    if (!rec.fullName) errors.push('Full name is required — the report is addressed to the student.')
    if (rec.subjects.length === 0) errors.push('At least one subject is required.')
    rec.subjects.forEach(function (s, i) {
      if (!s.subject) errors.push('Subject ' + (i + 1) + ': subject name is empty.')
      if (s.mark !== null && (s.mark < 0 || s.mark > 100)) errors.push('Subject ' + (i + 1) + ': mark must be between 0 and 100.')
    })
    var seen = {}
    rec.subjects.forEach(function (s) {
      if (s.subject && seen[s.subject]) warnings.push('Duplicate subject recorded: ' + s.subject + '.')
      seen[s.subject] = true
    })
    rec.interests.forEach(function (it, i) {
      if (!it.country) warnings.push('Interest ' + (i + 1) + ': no country selected, so destination rules cannot fire.')
      if (!it.field) warnings.push('Interest ' + (i + 1) + ': no field selected, so course rules cannot fire.')
    })
    if (rec.targetAtar !== null && rec.computedAtar !== null && rec.computedAtar > rec.targetAtar + 20) {
      warnings.push('The computed ATAR exceeds the target by more than 20 points — confirm the target was entered in the same direction.')
    }
    Object.keys(compileErrors).forEach(function (id) {
      errors.push('Rule "' + id + '" cannot be evaluated: ' + compileErrors[id] + '.')
    })
    return { errors: errors, warnings: warnings }
  }

  /* ---------------------------------------------------------------------
   * Evaluation.
   * -------------------------------------------------------------------*/
  function evaluate(rec) {
    var scope = { record: rec }
    var helpers = buildHelpers(rec, scope)
    return R.rules.map(function (rule) {
      var outcome = { rule: rule, fired: false, reason: '' }
      if (rule.enabled === false) { outcome.reason = 'disabled in catalog'; return outcome }
      if (compileErrors[rule.id]) { outcome.reason = 'compile error: ' + compileErrors[rule.id]; return outcome }
      try {
        outcome.fired = !!compiled[rule.id](rec, helpers)
      } catch (error) {
        outcome.reason = 'threw: ' + error.message
      }
      return outcome
    })
  }

  /* ---------------------------------------------------------------------
   * ATAR conversion.
   *
   * Two things this refuses to do, both because the alternative is a confident
   * wrong number:
   *   - It will not answer outside the calibrated span. The curve turns over at
   *     the top, so a perfect aggregate would otherwise convert DOWN to ~97.9.
   *     Returning null lets the page say "outside the calibrated range".
   *   - It will not print a figure without the caveat. `calibrationCheck` runs at
   *     load; if it failed, `atarAvailable()` is false and every caller must
   *     handle that rather than falling through to arithmetic on a bad curve.
   * -------------------------------------------------------------------*/
  function atarAvailable() {
    return !!(R.calibrationCheck && R.calibrationCheck.ok)
  }

  function aggregateToAtar(sum) {
    if (!atarAvailable()) return null
    var range = R.calibration.saneRange
    if (!(sum >= range[0] && sum <= range[1])) return null
    var c = R.calibration.coefficients
    var value = 0
    for (var i = 0; i < c.length; i++) value += c[i] * Math.pow(sum, i)
    if (isNaN(value)) return null
    return Math.max(R.calibration.clamp[0], Math.min(R.calibration.clamp[1], value))
  }

  /* The inverse: what aggregate does a target ATAR need? Solved by bisection
   * rather than algebra — inverting a degree-6 polynomial in closed form is more
   * code and more ways to be wrong, and the curve is monotonic where we allow it.
   * Returns null when the target is not reachable inside the calibrated span. */
  function atarToAggregate(target) {
    if (!atarAvailable()) return null
    if (typeof target !== 'number' || isNaN(target)) return null
    var lo = R.calibration.saneRange[0]
    var hi = R.calibration.saneRange[1]
    var atLo = aggregateToAtar(lo)
    var atHi = aggregateToAtar(hi)
    if (atLo === null || atHi === null) return null
    if (target < atLo || target > atHi) return null
    for (var i = 0; i < 80; i++) {
      var mid = (lo + hi) / 2
      if (aggregateToAtar(mid) < target) lo = mid
      else hi = mid
    }
    return (lo + hi) / 2
  }

  /* The best aggregate: the top N marks, only from subjects that count. A mark
   * entered as a percentage of a different maximum is not comparable, so
   * `aggregateMax` defines what a full mark is and anything above it is a likely
   * data-entry error rather than a very good student. */
  function bestAggregate(rec) {
    var n = R.calibration.aggregateSize
    var marks = rec.subjects
      .map(function (s) { return s.mark })
      .filter(function (m) {
        return typeof m === 'number' && !isNaN(m) && m >= 0 && m <= R.calibration.aggregateMax
      })
      .sort(function (a, b) { return b - a })
    if (marks.length < n) return null
    return marks.slice(0, n).reduce(function (a, b) { return a + b }, 0)
  }

  /* Everything the ATAR panel and the rules both need, computed once. `status`
   * is the honest word for what happened, so the UI never has to infer it.
   *
   * The target side is computed BEFORE the range guard, deliberately. Whether
   * the current aggregate can be converted and whether the target can be
   * answered are separate questions: `atarToAggregate` depends only on the
   * target, so a student whose marks sit below the calibrated floor can still be
   * told exactly what aggregate their goal needs. Returning early there — which
   * this function used to do — withheld the one number that was computable, and
   * that is precisely the student who most needs it. */
  function atarPicture(rec) {
    var agg = bestAggregate(rec)
    if (!atarAvailable()) {
      return { status: 'unavailable', aggregate: agg, atar: null, reason: 'calibration failed its own check' }
    }
    if (agg === null) {
      return {
        status: 'insufficient', aggregate: null, atar: null,
        reason: 'need ' + R.calibration.aggregateSize + ' countable subject marks',
      }
    }
    var target = rec.targetAtar
    var needed = typeof target === 'number' ? atarToAggregate(target) : null
    var perSubject = needed === null ? null : needed / R.calibration.aggregateSize
    var targetSide = {
      target: target,
      neededAggregate: needed,
      neededPerSubject: perSubject,
    }
    var atar = aggregateToAtar(agg)
    if (atar === null) {
      var range = R.calibration.saneRange
      return {
        status: 'out-of-range', aggregate: agg, atar: null,
        reason: 'aggregate ' + agg.toFixed(R.calibration.display.aggregate) + ' is outside the calibrated span ' +
          range[0] + '-' + range[1],
        target: targetSide.target,
        neededAggregate: targetSide.neededAggregate,
        neededPerSubject: targetSide.neededPerSubject,
        gapToTarget: needed === null ? null : needed - agg,
      }
    }
    targetSide.status = 'ok'
    targetSide.aggregate = agg
    targetSide.atar = atar
    targetSide.gapToTarget = needed === null ? null : needed - agg
    return targetSide
  }

  /* ---------------------------------------------------------------------
   * The record as a spreadsheet row.
   *
   * The original keeps one workbook per student, so a teacher's normal move is
   * to open a spreadsheet. A markdown report cannot be sorted or filtered across
   * a cohort; a CSV can. This is the export that makes the tool usable in the
   * workflow the original lived in, without asking anyone to hand-write JSON.
   * -------------------------------------------------------------------*/
  function recordToRow(rec) {
    var interest = (rec.interests && rec.interests[0]) || {}
    var marks = (rec.subjects || []).map(function (s) { return s.mark })
      .filter(function (m) { return typeof m === 'number' })
      .sort(function (a, b) { return b - a })
    var agg = marks.length >= R.calibration.aggregateSize
      ? marks.slice(0, R.calibration.aggregateSize).reduce(function (a, b) { return a + b }, 0)
      : null
    var atar = agg === null ? null : aggregateToAtar(agg)
    return {
      name: rec.fullName || '',
      country: interest.country || '',
      field: interest.field || '',
      university: interest.university || '',
      targetAtar: rec.targetAtar === null || rec.targetAtar === undefined ? '' : rec.targetAtar,
      computedAtar: rec.computedAtar === null || rec.computedAtar === undefined ? '' : rec.computedAtar,
      subjectCount: (rec.subjects || []).length,
      aggregate: agg === null ? '' : agg.toFixed(R.calibration.display.aggregate),
      convertedAtar: atar === null ? '' : atar.toFixed(R.calibration.display.atar),
      subjects: (rec.subjects || []).map(function (s) {
        return s.subject + ':' + (typeof s.mark === 'number' ? s.mark : '')
      }).join(' '),
      notes: rec.notes || '',
    }
  }

  var CSV_HEADERS = ['name', 'country', 'field', 'university', 'targetAtar',
                     'computedAtar', 'subjectCount', 'aggregate', 'convertedAtar',
                     'subjects', 'notes']

  /* RFC 4180 quoting: wrap when the value contains a comma, quote, CR or LF, and
   * double any inner quote. A name with a comma in it silently shifting every
   * later column is the classic way a CSV export corrupts a dataset. */
  function csvCell(value) {
    var s = value === null || value === undefined ? '' : String(value)
    if (/[",\r\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"'
    return s
  }

  function recordToCsv(rec) {
    var row = recordToRow(rec)
    return CSV_HEADERS.map(function (h) { return csvCell(row[h]) }).join(',') + '\r\n'
  }

  /* ---------------------------------------------------------------------
   * Report assembly. Same principle as the original — emit only what fired,
   * in domain order — plus one thing it lacked: every paragraph carries the
   * id of the rule that produced it.
   * -------------------------------------------------------------------*/
  var generated = null

  function buildReport(rec, results) {
    var order = {}
    R.domains.forEach(function (d) { order[d.id] = d.order })
    var fired = results.filter(function (r) { return r.fired }).sort(function (a, b) {
      var da = order[a.rule.domain] || 999
      var db = order[b.rule.domain] || 999
      return da - db
    })

    var lines = []
    lines.push(R.meta.title.toUpperCase())
    lines.push('Advising report for ' + (rec.fullName || '(unnamed)'))
    if (rec.studentId) lines.push('Student ID: ' + rec.studentId)
    lines.push('Generated: ' + new Date().toLocaleString())
    lines.push('')

    var currentDomain = null
    fired.forEach(function (item) {
      var d = R.domains.filter(function (x) { return x.id === item.rule.domain })[0]
      var label = d ? d.label : item.rule.domain
      if (label !== currentDomain) {
        lines.push('')
        lines.push('— ' + label.toUpperCase() + ' —')
        currentDomain = label
      }
      lines.push('')
      lines.push(interpolate(item.rule.advice, rec))
      lines.push('   [rule: ' + item.rule.id + ' · source: ' + item.rule.source + ']')
    })

    if (fired.length === 0) lines.push('No rule conditions were met. The record may be too sparse to advise on.')

    var picture = atarPicture(rec)
    if (picture.status !== 'insufficient') {
      lines.push('')
      lines.push('— AGGREGATE CONVERSION —')
      lines.push('')
      lines.push('Best ' + R.calibration.aggregateSize + ' subject marks total ' +
        (picture.aggregate === null ? '(not countable)' : picture.aggregate.toFixed(1)) + '.')
      if (picture.status === 'ok') {
        lines.push('Indicative ATAR: ' + picture.atar.toFixed(2))
        if (picture.neededAggregate !== null) {
          lines.push('Target ' + picture.target + ' needs an aggregate of ' +
            picture.neededAggregate.toFixed(1) + ' (' + picture.neededPerSubject.toFixed(1) +
            ' per subject across ' + R.calibration.aggregateSize + ').')
          lines.push(picture.gapToTarget > 0
            ? 'That is ' + picture.gapToTarget.toFixed(1) + ' above where you are.'
            : 'You are already ' + Math.abs(picture.gapToTarget).toFixed(1) + ' above what that target needs.')
        } else if (typeof picture.target === 'number') {
          lines.push('Target ' + picture.target + ' is outside the range this conversion can answer for.')
        }
        lines.push('   [' + R.calibration.caveat + ']')
      } else {
        lines.push('No ATAR is reported: ' + picture.reason + '.')
        lines.push('   [Refusing to guess is the point — a number here would look authoritative and be wrong.]')
      }
    }

    // Whatever the adviser wrote lands at the end, after every generated
    // paragraph, so it reads as an addition to the report rather than as one of
    // the tool's own claims. That distinction matters: the notes are a person's
    // words, and the report labels everything else with the rule that produced it.
    if (rec.notes && String(rec.notes).trim()) {
      lines.push('')
      lines.push('— NOTES —')
      lines.push('')
      lines.push(String(rec.notes).trim())
    }

    return { text: lines.join('\n'), fired: fired }
  }

  function renderReport() {
    var rec = readRecord()
    var check = validate(rec)

    var box = $('validationBox')
    box.innerHTML = ''
    if (check.errors.length) {
      box.appendChild(el('div', { 'class': 'note err', html: '<strong>Cannot generate a report:</strong><ul style="margin:6px 0 0 18px">' +
        check.errors.map(function (e) { return '<li>' + escapeHtml(e) + '</li>' }).join('') + '</ul>' }))
    } else if (check.warnings.length) {
      box.appendChild(el('div', { 'class': 'note', html: '<strong>Worth checking:</strong><ul style="margin:6px 0 0 18px">' +
        check.warnings.map(function (e) { return '<li>' + escapeHtml(e) + '</li>' }).join('') + '</ul>' }))
    } else {
      box.appendChild(el('div', { 'class': 'note ok', text: 'Record passes validation.' }))
    }

    var results = evaluate(rec)
    var report = buildReport(rec, results)
    generated = { record: rec, report: report, results: results, check: check }

    // Report tab
    $('reportBody').innerHTML = ''
    report.fired.forEach(function (item) {
      var d = R.domains.filter(function (x) { return x.id === item.rule.domain })[0]
      $('reportBody').appendChild(el('p', { 'class': 'advice', html:
        '<span class="badge">' + escapeHtml(d ? d.label : item.rule.domain) + '</span>' +
        escapeHtml(interpolate(item.rule.advice, rec)) }))
      $('reportBody').appendChild(el('span', { 'class': 'src',
        text: 'rule: ' + item.rule.id + ' · source: ' + item.rule.source +
              (item.rule.verified ? ' · verified ' + item.rule.verified : ' · NOT VERIFIED') }))
    })
    $('reportStamp').textContent = (function(){
        var zh = (typeof LANG !== 'undefined' && LANG === 'zh')
        return (zh ? '（命中 ' : '(') + report.fired.length
             + (zh ? ' / ' : ' of ') + R.rules.length
             + (zh ? ' 条规则）' : ' rules fired)')
      })()

    // Coverage tab
    renderCoverage(results)

    $('reportWarnings').innerHTML = check.errors.length
      ? '<div class="note err">This report was generated from a record with ' + check.errors.length + ' validation error(s). Treat it as a draft.</div>'
      : ''

    showTab('report')
  }

  /* The coverage view is a catalogue listing, not part of the report: it shows
   * every rule in the file, whether the record in front of the reader trips it,
   * and whether a human has confirmed its claim. It used to be built inside
   * renderReport only, so opening the tab before pressing the button showed an
   * empty table and a blank summary — which reads as a broken page rather than
   * as "nothing generated yet". It is now rendered on arrival and again whenever
   * the tab is opened, from the form as it currently stands.
   *
   * `firedCount` is derived from `results` rather than taken from a report, so
   * the view does not depend on a report having been generated at all. */
  function renderCoverage(results) {
    var rows = $('coverageRows')
    if (!rows) return
    var firedCount = results.filter(function (r) { return r.fired }).length
    rows.innerHTML = ''
    results.forEach(function (item) {
      var tr = el('tr')
      var d = R.domains.filter(function (x) { return x.id === item.rule.domain })[0]
      tr.appendChild(el('td', { text: d ? d.label : item.rule.domain }))
      var cell = el('td')
      cell.appendChild(el('div', { text: item.rule.title || item.rule.id }))
      cell.appendChild(el('div', { 'class': 'muted', html: '<code>' + escapeHtml(item.rule.id) + '</code> · ' + escapeHtml(item.rule.when) }))
      if (item.reason) cell.appendChild(el('div', { 'class': 'muted', text: '→ ' + item.reason }))
      tr.appendChild(cell)
      tr.appendChild(el('td', { html: item.fired ? '<span class="badge">yes</span>' : '<span class="badge off">no</span>' }))
      tr.appendChild(el('td', { html: item.rule.verified
        ? '<span class="badge">' + escapeHtml(item.rule.verified) + '</span>'
        : '<span class="badge warn">verify</span>' }))
      rows.appendChild(tr)
    })

    var unverified = R.rules.filter(function (r) { return !r.verified }).length
    var disabled = R.rules.filter(function (r) { return r.enabled === false }).length
    $('coverageSummary').innerHTML =
      '<div class="note' + (unverified ? '' : ' ok') + '"><strong>' + R.rules.length + ' rules in catalog · ' +
      firedCount + ' fired · ' + unverified + ' awaiting verification · ' + disabled + ' disabled.</strong>' +
      (unverified ? ' Rules marked <em>verify</em> make a factual claim that a human has not yet confirmed against a current source.' : '') +
      '</div>'
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]
    })
  }

  /* -------------------------- assessment tracker ---------------------- */
  function importanceFor(weight) {
    if (typeof weight !== 'number') return null
    for (var i = 0; i < R.importanceBands.length; i++) {
      if (weight < R.importanceBands[i].max) return R.importanceBands[i]
    }
    return R.importanceBands[R.importanceBands.length - 1]
  }

  function addAssessRow(preset) {
    preset = preset || {}
    var tr = el('tr')
    var name = el('input', { type: 'text', 'class': 'a-name', placeholder: 'e.g. Topic test 2' })
    name.value = preset.name || ''
    var weight = el('input', { type: 'number', 'class': 'a-weight', min: '0', max: '100' })
    weight.value = preset.weight === undefined ? '' : preset.weight
    var due = el('input', { type: 'date', 'class': 'a-due' })
    due.value = preset.due || ''
    var imp = el('td', { 'class': 'muted', text: '—' })
    var urg = el('select', { 'class': 'a-urg' }, [])
    urg.appendChild(options(['1', '2', '3', '4', '5'], String(preset.urgency || '3'), undefined))
    var done = el('input', { type: 'checkbox', 'class': 'a-done' })
    done.checked = !!preset.done
    var action = el('td', { 'class': 'muted', text: '—' })
    var bin = el('button', { 'class': 'ghost mini', text: '×' })

    function refresh() {
      var w = numOrNull(weight.value)
      var band = importanceFor(w)
      imp.textContent = band ? band.label : '—'
      var level = band ? band.level : null
      var u = Number(urg.value)
      if (done.checked) {
        action.textContent = 'Completed.'
        action.className = 'muted'
      } else if (level) {
        action.textContent = R.matrix[u][level]
        action.className = ''
      } else {
        action.textContent = 'Enter a weight to get an action.'
        action.className = 'muted'
      }
      summariseAssessments()
    }
    ;[weight, urg, done].forEach(function (node) { node.addEventListener('input', refresh) })
    bin.addEventListener('click', function () { tr.remove(); summariseAssessments() })

    tr.appendChild(el('td', {}, [name]))
    tr.appendChild(el('td', {}, [weight]))
    tr.appendChild(el('td', {}, [due]))
    tr.appendChild(imp)
    tr.appendChild(el('td', {}, [urg]))
    tr.appendChild(el('td', {}, [done]))
    tr.appendChild(action)
    tr.appendChild(el('td', {}, [bin]))
    $('assessRows').appendChild(tr)
    refresh()
  }

  function summariseAssessments() {
    var rows = $('assessRows').querySelectorAll('tr')
    var outstanding = 0
    var critical = 0
    var now = Date.now()
    Array.prototype.forEach.call(rows, function (tr) {
      if (tr.querySelector('.a-done').checked) return
      var w = numOrNull(tr.querySelector('.a-weight').value)
      var band = importanceFor(w)
      if (!band) return
      outstanding++
      if (band.level >= 4 && Number(tr.querySelector('.a-urg').value) >= 4) critical++
      else if (band.level >= 4) critical++
      var due = tr.querySelector('.a-due').value
      if (due && new Date(due).getTime() < now) tr.style.background = 'var(--bad-soft)'
      else tr.style.background = ''
    })
    $('trackerSummary').textContent = outstanding === 0
      ? 'No outstanding assessments recorded.'
      : outstanding + ' outstanding · ' + critical + ' at major-or-critical weight. Rows past their due date are shaded.'
  }

  /* -------------------------- tabs, storage, export ------------------- */
  function showTab(which) {
    ['student', 'report', 'tracker', 'coverage'].forEach(function (t) {
      $('tab-' + t).classList.toggle('hidden', t !== which)
    })
    Array.prototype.forEach.call(document.querySelectorAll('nav.tabs button'), function (b) {
      b.setAttribute('aria-selected', String(b.dataset.tab === which))
    })
  }

  var STORAGE_KEY = 'advising-workbook-record-v1'

  function sample() {
    return {
      fullName: 'Sample Student',
      studentId: 'S-000000',
      year11School: 'Sample Secondary College',
      englishFirstLanguage: false,
      previousIntake: 'September intake',
      targetAtar: 88,
      stillDeciding: false,
      fundingSecured: false,
      interests: [
        { country: 'Australia', field: 'Engineering', university: 'Curtin University' },
        { country: 'United Kingdom', field: 'Engineering', university: 'University of Manchester' },
      ],
      // 科目**必须用课程代码**，不能用全名。
      // 科目那一格是下拉，选项来自 R.vocabularies.subjects（只有 ATMAM 这类代码），
      // 而校验也拿这份词表比对。示例原来写 'Mathematics Methods' 这种全名，
      // 载入后下拉全部落回「— 科目 —」，点「生成报告」直接报
      // 「无法生成报告：至少需要填写一门科目。」—— 工具自己给的输入自己判非法。
      // 低分学生走查实测到，新用户第一分钟就撞墙。
      subjects: [
        { subject: 'ATMAM', mark: 82 },
        { subject: 'ATPHY', mark: 74 },
        { subject: 'ATCHE', mark: 58 },
        { subject: 'ATEALD', mark: 71 },
        { subject: 'ATPSY', mark: 66 },
      ],
      year11: { English: 71, Mathematics: 82 },
      priorResults: { Chemistry: 52 },
    }
  }

  /* -------------------------- wiring ---------------------------------- */
  $('addInterest').addEventListener('click', function () { addInterestRow() })
  $('addSubject').addEventListener('click', function () { addSubjectRow() })
  $('btnGenerate').addEventListener('click', renderReport)
  $('btnSample').addEventListener('click', function () { writeRecord(sample()); renderReport() })
  $('btnClear').addEventListener('click', function () { writeRecord({ interests: [], subjects: [], year11: {}, priorResults: {} }); $('validationBox').innerHTML = '' })
  $('btnSave').addEventListener('click', function () {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(readRecord()))
      $('validationBox').innerHTML = '<div class="note ok">Saved to this browser only. Nothing was sent anywhere.</div>'
    } catch (e) {
      $('validationBox').innerHTML = '<div class="note err">Could not save: ' + escapeHtml(e.message) + '</div>'
    }
  })
  $('btnLoad').addEventListener('click', function () {
    var raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) { $('validationBox').innerHTML = '<div class="note">Nothing saved in this browser yet.</div>'; return }
    writeRecord(JSON.parse(raw))
  })
  $('btnPrint').addEventListener('click', function () { window.print() })
  $('btnCopy').addEventListener('click', function () {
    if (generated) navigator.clipboard.writeText(generated.report.text)
  })
  $('btnDownload').addEventListener('click', function () {
    if (!generated) return
    var blob = new Blob([generated.report.text], { type: 'text/markdown' })
    var a = el('a', { href: URL.createObjectURL(blob), download: 'advising-report.md' })
    document.body.appendChild(a); a.click(); a.remove()
  })
  // The record as one spreadsheet row. Header included so a cohort of these can
  // be concatenated into a single CSV a teacher can sort and filter.
  //
  // Wired through on(), not addEventListener: the report tab exists on both
  // pages but the guest page has no CSV button, and an unguarded listener on a
  // missing node is what once killed the whole engine on the guest page.
  on('btnCsv', 'click', function () {
    var rec = readRecord()
    var csv = CSV_HEADERS.join(',') + '\r\n' + recordToCsv(rec)
    // The BOM is what makes Excel open UTF-8 correctly; without it a Chinese
    // name arrives as mojibake, which is the one thing that would make this
    // export useless for the people most likely to use it.
    var blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
    var a = el('a', { href: URL.createObjectURL(blob), download: 'advising-record.csv' })
    document.body.appendChild(a); a.click(); a.remove()
  })
  Array.prototype.forEach.call(document.querySelectorAll('nav.tabs button'), function (b) {
    b.addEventListener('click', function () {
      showTab(b.dataset.tab)
      // Opened fresh, the coverage tab must describe the form as it now stands.
      // Rendering it only at load would list rules against a record the reader
      // has since edited, which is worse than an empty table.
      if (b.dataset.tab === 'coverage') renderCoverage(evaluate(readRecord()))
    })
  })

  $('appTitle').textContent = R.meta.title
  $('appSub').textContent = R.meta.subtitle + ' · v' + R.meta.version + ' · ' + R.meta.contentPolicy

  writeRecord({ interests: [], subjects: [], year11: {}, priorResults: {} })
  // The coverage tab is a catalogue, not a report, so it can be filled on
  // arrival: the reader sees the full rule list, what the current (empty) form
  // trips, and which claims are still unverified, without pressing anything.
  renderCoverage(evaluate(readRecord()))
})()
