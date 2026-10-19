/* ============================================================================
 * advising-rules.js — the SINGLE SOURCE OF TRUTH for this advising engine.
 * ----------------------------------------------------------------------------
 * Every piece of advice lives here as data, not inside engine code. Adding,
 * editing, disabling, or citing a rule means editing THIS FILE ONLY.
 *
 * Architecture note: the engine never contains advice text. It walks this
 * table, evaluates each `when` expression against the student record, and
 * prints the `advice` of every rule that fires. That separation is the whole
 * point — it is what makes the advice auditable and diffable.
 *
 * CONTENT POLICY (read before editing):
 *   - Every string below is ORIGINALLY WRITTEN for this template. It is
 *     illustrative sample copy, not a policy source.
 *   - All numbers are PLACEHOLDERS. Verify against current official material
 *     before any real use, and update `verified` when you do.
 *   - `source` names where a claim must be confirmed. If a rule cannot be
 *     sourced, either find the source or delete the rule.
 * ==========================================================================*/

window.ADVISING = (function () {
  'use strict'

  /* --------------------------------------------------------------------------
   * 1. The catalog. `label` is what the advisor sees; `order` is sort order.
   * ------------------------------------------------------------------------*/
  const domains = [
    { id: 'completeness', label: 'Submission completeness', order: 10 },
    { id: 'destination', label: 'Destination & applications', order: 20 },
    { id: 'course', label: 'Course-specific requirements', order: 30 },
    { id: 'language', label: 'Language proficiency', order: 40 },
    { id: 'funding', label: 'Scholarships & funding', order: 50 },
    { id: 'performance', label: 'Academic performance', order: 60 },
    { id: 'skills', label: 'Skills & readiness', order: 70 },
    { id: 'wellbeing', label: 'Study approach & wellbeing', order: 80 },
  ]

  /* --------------------------------------------------------------------------
   * 1b. Field roadmap.
   *
   *    The source workbook has a SKILLS ROADMAP sheet shaped as one template per
   *    field: careers, supercurricular activities, the skills that matter, and
   *    why the field is future-proof. Only one field is filled in there. This is
   *    the same SHAPE with our own copy for the fields the form offers, so the
   *    module is general rather than a single worked example.
   *
   *    Entries are keyed by the same field vocabulary the form uses, so a typo in
   *    a key means the module goes silent for that field. The build asserts every
   *    vocabulary field has an entry.
   * ------------------------------------------------------------------------*/
  const ROADMAP_MARKER = null // replaced at build time

  /* --------------------------------------------------------------------------
   * 1c. Pathways and timelines.
   *
   *    The source workbook's OPTIONS AND OPPORTUNITIES sheet is a set of pathway
   *    blocks (study in Australia, TAFE, UK applications), each with a short
   *    orientation and a "useful links" column pointing at the official service.
   *    The links are the useful part and they are public services, so they are
   *    reproduced here as entry points; the surrounding prose is ours.
   *
   *    Every link below was requested and checked. Dead ones are removed rather
   *    than shipped hopeful — a broken official link is worse than no link.
   * ------------------------------------------------------------------------*/
  const OPPORTUNITIES_MARKER = null // replaced at build time

  /* --------------------------------------------------------------------------
   * 2. Controlled vocabularies. Validation uses these, so a typo is caught
   *    instead of silently failing to match a rule. This replaces the original
   *    design's unguarded exact-string comparisons.
   * ------------------------------------------------------------------------*/
  const vocabularies = {
    countries: [
      'Australia', 'United Kingdom', 'United States', 'Canada',
      'Ireland', 'New Zealand', 'Malaysia', 'Singapore', 'Japan', 'Other',
    ],
    fields: [
      'Medicine', 'Dentistry', 'Law', 'Engineering', 'Computer Science',
      'Business', 'Psychology', 'Nursing', 'Architecture', 'Sciences',
      'Humanities', 'Education', 'Undecided',
    ],
    // ── subjects: the ATAR subjects, by the code the school uses ─────────────
    // Taken from the source workbook's own list (LISTS!A3:A15) and confirmed
    // against the screen it drives: "Top 4 ATAR Subjects (Choose from list)".
    // The workbook's list continues past these with a GTCSC/GT…/EPSGS block after
    // a row of asterisks; those are General courses and **their marks do not
    // count toward an ATAR**, so they are deliberately absent here. That absence
    // is doing real work: the best-four aggregate is computed from whatever is
    // recorded, so a General subject that could be typed in would silently
    // inflate the aggregate. A pick-list makes it unrepresentable instead.
    //
    // Codes only, no names — the workbook shows codes only, and inventing
    // expansions for courses whose syllabus we have not read would be inventing
    // fact. Five are sourced: ATMAM is "Mathematics Methods" (the eLearn course
    // name 260129-ATMAM), and ATPHY/ATHBY/ATCSC/ATEALD match the Physics, Human
    // Biology, Computer Science and English folders in the course archive.
    //
    // There was a `level` vocabulary here before this one:
    // ['Year 11', 'September intake', 'January intake']. It went with the column
    // it fed. Three unrelated things had been bundled into it — a year level and
    // two intake names — and the workbook only ever asks about intake at STUDENT
    // level ("If you were part of the Sept/ Head Start intakes, please check this
    // box"), never per subject.
    subjects: [
      'ATACF', 'ATBME', 'ATCHE', 'ATCSC', 'ATEALD', 'ATECO', 'ATENG',
      'ATHBY', 'ATMAA', 'ATMAM', 'ATMAS', 'ATPHY', 'ATPSY',
    ],
  }

  /* --------------------------------------------------------------------------
   * 3. Thresholds. Named once, referenced by rules. Numbers scattered through
   *    conditions are how two rules end up disagreeing about what "weak" means
   *    — an inconsistency this catalog originally had, found by verification
   *    rather than by reading. Change a policy figure here, not in a rule.
   * ------------------------------------------------------------------------*/
  const thresholds = {
    weakMark: 60,          // a subject result at or below this is materially weak
    targetGapPoints: 5,    // standing this far below target is worth raising
    subjectsForAggregate: 4,
    heavyLoadSubjects: 6,
    priorIntakeWeakMark: 60,
    atarMarginPoints: 2,   // how close to a stated minimum counts as marginal
  }

  /* --------------------------------------------------------------------------
   * 4. Subject capabilities.
   *
   *    A "capability" is a kind of preparation a course can require, expressed
   *    against AUSMAT subject names. Rules ask for a capability; the mapping
   *    from capability to subjects lives here, once.
   *
   *    Why capabilities rather than a list of courses and their prerequisites:
   *    the institutional workbook carries a course database whose prerequisite
   *    column is free text. Profiling it found only a handful of rows in any
   *    machine-readable shape (English-YES Mathematics-YES Science/Other-NO)
   *    and a dozen more in prose ("Mathematics ... and at least one of
   *    Chemistry or Physics are formal prerequisites"). Parsing that prose into
   *    flags would manufacture certainty the source does not have. What the
   *    advisor actually needs is the capability question asked reliably, with
   *    the unmapped cases surfaced instead of guessed.
   *
   *    Extend `capabilities` as real prerequisites are confirmed. Every rule
   *    consuming a capability then covers the new subject automatically.
   * ------------------------------------------------------------------------*/
  const capabilities = {
    // Keyed by the subject CODE, because that is what the form records now.
    //
    // These lists used to hold course NAMES with synonyms ('Mathematics',
    // 'Mathematics Methods', 'Add Maths', 'Additional Mathematics' …). The
    // synonyms existed only because the subject field was free text and a student
    // might type any of them; a pick-list makes every one of them unreachable
    // while keeping the matching exact, which is the point. Anything typed by
    // hand matched by string equality, so 'Maths' silently satisfied nothing and
    // the prerequisite rules went quiet without saying why.
    //
    // KNOWN COARSENESS: mathematics covers Applications as well as Methods and
    // Specialist. WACE treats those as different depths, and an engineering
    // programme that asks for Methods is not satisfied by Applications. The
    // workbook's own course database does not state the distinction either, so
    // splitting it here would be inventing a requirement it never recorded.
    mathematics: {
      label: 'Mathematics',
      subjects: ['ATMAA', 'ATMAM', 'ATMAS'],
    },
    physicalScience: {
      label: 'a physical science',
      subjects: ['ATPHY', 'ATCHE'],
    },
    chemistry: {
      label: 'Chemistry',
      subjects: ['ATCHE'],
    },
    biology: {
      label: 'Biology',
      subjects: ['ATHBY'],
    },
    english: {
      label: 'English',
      subjects: ['ATENG', 'ATEALD'],
    },
    computing: {
      label: 'Computing',
      subjects: ['ATCSC'],
    },
  }

  /* --------------------------------------------------------------------------
   * 5. Course expectations.
   *
   *    Per field of study, the capabilities it normally expects, optional extras
   *    worth raising, and — importantly — whether a minimum ATAR can be stated
   *    at all. `namedAtar` defaults to null, meaning "this tool has no current
   *    figure". A rule then says so rather than inventing a number.
   *
   *    Every entry carries `source` because a course expectation is a factual
   *    claim, and a stale one sends a student to the wrong programme.
   *    `verified: null` keeps it visible in the coverage view until a human
   *    checks it against the current institution page.
   * ------------------------------------------------------------------------*/
  const courseExpectations = {
    Engineering: {
      expects: ['mathematics', 'physicalScience'],
      optional: ['chemistry'],
      namedAtar: null,
      source: 'Confirm each programme’s assumed-knowledge statement',
      verified: null,
    },
    'Computer Science': {
      expects: ['mathematics'],
      optional: ['computing', 'physicalScience'],
      namedAtar: null,
      source: 'Confirm each programme’s prerequisite statement',
      verified: null,
    },
    Medicine: {
      expects: ['chemistry', 'english'],
      optional: ['biology', 'mathematics'],
      namedAtar: null,
      source: 'Confirm prerequisites and admissions-test requirements per university',
      verified: null,
    },
    Dentistry: {
      expects: ['chemistry'],
      optional: ['biology', 'mathematics'],
      namedAtar: null,
      source: 'Confirm prerequisites and admissions-test requirements per university',
      verified: null,
    },
    Nursing: {
      expects: ['english'],
      optional: ['biology', 'mathematics'],
      namedAtar: null,
      source: 'Confirm per-institution English and science requirements',
      verified: null,
    },
    Sciences: {
      expects: ['mathematics'],
      optional: ['chemistry', 'physicalScience', 'biology'],
      namedAtar: null,
      source: 'Confirm the prerequisites of the specific science programme',
      verified: null,
    },
    Psychology: {
      expects: ['english'],
      optional: ['mathematics', 'biology'],
      namedAtar: null,
      source: 'Confirm per-institution prerequisites',
      verified: null,
    },
    Business: {
      expects: [],
      optional: ['mathematics'],
      namedAtar: null,
      source: 'Confirm per-institution prerequisites',
      verified: null,
    },
    Law: {
      expects: [],
      optional: ['english'],
      namedAtar: null,
      source: 'Confirm per-institution prerequisites and any admissions test',
      verified: null,
    },
    Architecture: {
      expects: ['mathematics'],
      optional: ['physicalScience'],
      namedAtar: null,
      source: 'Confirm per-institution prerequisites, including any portfolio',
      verified: null,
    },
    Education: {
      expects: ['english'],
      optional: ['mathematics'],
      namedAtar: null,
      source: 'Confirm per-institution prerequisites',
      verified: null,
    },
    Humanities: {
      expects: ['english'],
      optional: [],
      namedAtar: null,
      source: 'Confirm per-institution prerequisites',
      verified: null,
    },
    Undecided: {
      expects: [],
      optional: [],
      namedAtar: null,
      source: 'internal',
      verified: '2026-01-01',
    },
  }

  /* --------------------------------------------------------------------------
   * 6. Rules. Each rule is one condition + one piece of advice.
   *
   *    when    — expression over the student record. This is a small expression
   *              grammar, NOT JavaScript: no arrow functions, no statements, no
   *              assignments, no eval. Calling a callback is therefore
   *              impossible by design, which is why comparisons against list
   *              elements go through helpers that CONTAIN the path to compare:
   *
   *                anyInterest(path[, value])   any interests[] element matches
   *                                             `path` — a STRING naming the
   *                                             field — optionally against
   *                                             value (single value or array)
   *                countSubject(prefix)         subjects whose level starts with
   *                                             prefix
   *                anyScoreBelow(n)             any subject mark below n
   *                anyValueBelow(object, n)     any numeric value in an object
   *                                             below n
   *                hasSubject(name)             a subject with this name exists
   *                score(subject)               that subject's mark, or null
   *                anyInterestExpectationGap(path, subjects)
   *                                             a stated course expectation needs
   *                                             a capability the student lacks
   *                anyInterestOptionalGap(path, subjects)
   *                                             a recommended capability is missing
   *                                             while the required set is covered
   *                nearestAboveWithin(margin)   the nearest recorded minimum above
   *                                             the computed standing is within it
   *                anyInterestUnmatched()       a choice matches no library course
   *                record                       the student record itself
   *                T                            the thresholds table above
   *
   *                anyInterestMissing and belowStatedMinimum were both here and
   *                both went with the per-interest minimum ATAR field: no control
   *                ever set it, so anyInterestMissing was true on every record
   *                with a choice, and belowStatedMinimum could never be satisfied.
   *                The library answers both questions now.
   *
   *              The path is a plain STRING naming a field on the element. The
   *              helper resolves it per element, because the outer scope has no
   *              `i` and no other construct can bind one.
   *
   *              Examples:
   *                anyInterest("i.country", "Australia")
   *                anyInterest("i.field", ["Medicine", "Dentistry"])
   *                !anyInterest("i.country", ["Australia", "United Kingdom"])
   *                record.subjects.length >= T.subjectsForAggregate
   *                record.estimatedAtar < record.targetAtar - T.targetGapPoints
   *    advice  — shown when `when` is true. {{tokens}} interpolate from the
   *              record, e.g. {{fullName}} or {{targetAtar}}.
   *    source  — where a human must verify any factual claim, or 'internal'
   *              for process advice that is not a factual claim.
   *    verified— null, or an ISO date once a human confirmed the content.
   *
   *    A rule with `enabled: false` is kept for the record and shown in the
   *    coverage view as deliberately silent — never deleted just to hide it.
   * ------------------------------------------------------------------------*/
  const rules = [
    {
      id: 'form-incomplete',
      domain: 'completeness',
      title: 'Required fields outstanding',
      // Off, not removed. The coverage view still lists it, so the decision is on
      // the record rather than invisible. Both fields it was written against —
      // the student's name and their Year 11 school — were removed from the form
      // when the identity block went, and the one clause that survived, an empty
      // subject list, is already a hard validation error: a report cannot be
      // generated while it is true. Leaving it enabled would have printed "this
      // report is provisional" on every report, including complete ones.
      enabled: false,
      when: 'record.subjects.length === 0',
      advice:
        'This report is provisional because required fields are still blank. ' +
        'Advisor guidance is only as good as the information behind it.',
      source: 'internal',
      verified: '2026-01-01',
    },
    {
      id: 'subjects-fewer-than-four',
      domain: 'completeness',
      title: 'Fewer than four ATAR subjects recorded',
      when: 'record.subjects.length > 0 && record.subjects.length < T.subjectsForAggregate',
      advice:
        'You have recorded {{subjectCount}} ATAR subject(s). Most university ' +
        'aggregates are calculated from four or more, so confirm which subjects ' +
        'will count toward your aggregate.',
      source: 'Confirm the aggregate rules for your qualification',
      verified: null,
    },

    {
      id: 'dest-none-stated',
      domain: 'destination',
      title: 'No destination country given',
      when: 'record.interests.length === 0',
      advice:
        'No destination country has been recorded. Without one, visa timelines, ' +
        'language requirements and application deadlines cannot be assessed.',
      source: 'internal',
      verified: '2026-01-01',
    },
    {
      id: 'dest-uk',
      domain: 'destination',
      title: 'United Kingdom destination',
      when: 'anyInterest("i.country", "United Kingdom")',
      advice:
        'Applications to the United Kingdom go through a central admissions ' +
        'service rather than directly to each university. Expect to supply an ' +
        'academic reference and a personal statement, and note that a single ' +
        'application covers several choices. Confirm the current cycle deadlines ' +
        'with your advisor before you start writing.',
      source: 'Check the current admissions-service cycle deadlines',
      verified: '2026-09-25',
    },
    {
      id: 'dest-us',
      domain: 'destination',
      title: 'United States destination',
      when: 'anyInterest("i.country", "United States")',
      advice:
        'United States applications typically require standardised testing, ' +
        'essays, and references requested months in advance. Each university ' +
        'has its own form, so plan for several parallel applications.',
      source: 'Check each university’s admissions requirements',
      verified: '2026-09-25',
    },
    {
      id: 'dest-au',
      domain: 'destination',
      title: 'Australia destination',
      when: 'anyInterest("i.country", "Australia")',
      advice:
        'Australian applications are generally made per institution or through ' +
        'a state admissions centre. Offer rounds are scheduled, so the timing of ' +
        'your results release matters as much as the marks themselves.',
      source: 'Check the relevant state admissions centre schedule',
      verified: '2026-09-25',
    },

    {
      id: 'course-medicine',
      domain: 'course',
      title: 'Medicine or dentistry pathway',
      when: 'anyInterest("i.field", ["Medicine", "Dentistry"])',
      advice:
        'Medical and dental programmes usually add an aptitude or admissions ' +
        'test on top of academic results, and some institutions also interview. ' +
        'Registration windows for those tests close well before the application ' +
        'deadline, so this is the earliest item on your timeline.',
      source: 'Confirm test requirements and registration windows per university',
      verified: null,
    },
    {
      id: 'course-law',
      domain: 'course',
      title: 'Law pathway',
      when: 'anyInterest("i.field", "Law")',
      advice:
        'Law programmes often have no fixed subject prerequisites, but some ' +
        'jurisdictions require an additional admissions test. Confirm whether ' +
        'the universities you are considering require one.',
      source: 'Confirm per-university admissions test requirements',
      verified: null,
    },
    {
      id: 'course-engineering',
      domain: 'course',
      title: 'Engineering pathway',
      when: 'anyInterest("i.field", "Engineering")',
      advice:
        'Engineering degrees normally assume a strong mathematics background, ' +
        'and several expect physics as well. Check the assumed-knowledge ' +
        'statement for each programme rather than relying on the entry score alone.',
      source: 'Check each programme’s assumed knowledge statement',
      verified: '2026-09-25',
    },
    {
      id: 'course-undecided',
      domain: 'course',
      title: 'Field of study still undecided',
      // The "still deciding" checkbox went with the identity block. The two
      // conditions that remain are both read from the interests table itself: no
      // rows at all, or a row that names Undecided as the field.
      when: 'record.interests.length === 0 || anyInterest("i.field", "Undecided")',
      advice:
        'Being undecided at this stage is normal and workable. The useful move ' +
        'is to narrow by constraint rather than by preference: which subjects you ' +
        'are strongest in, which countries you can fund, and which prerequisite ' +
        'subjects you would need to keep open. Narrowing those three usually ' +
        'removes most of the field.',
      source: 'internal',
      verified: '2026-01-01',
    },

    {
      id: 'lang-non-english-destination',
      domain: 'language',
      title: 'Destination language may not be English',
      when: 'record.interests.length > 0 && !anyInterest("i.country", ["Australia","United Kingdom","United States","Canada","Ireland","New Zealand"])',
      advice:
        'Your stated destinations are not predominantly English-speaking. ' +
        'Programmes taught in another language normally require a proficiency ' +
        'certificate in that language, which takes time to obtain.',
      source: 'Confirm the language of instruction and required certificate',
      verified: null,
    },
    {
      id: 'lang-english-test',
      domain: 'language',
      title: 'English proficiency evidence may be required',
      // The old condition also tested `record.englishFirstLanguage !== true`,
      // which made it permanently true once that field was removed. The
      // destination list is the real trigger: these countries teach in English,
      // so their institutions ask most applicants for proficiency evidence
      // regardless of what was typed elsewhere. The advice no longer claims
      // anything about the reader's first language, which the form no longer
      // records and this tool must not assume.
      when: 'anyInterest("i.country", ["Australia","United Kingdom","United States","Canada","Ireland","New Zealand"])',
      advice:
        'These destinations teach in English, and most institutions there ask ' +
        'for evidence of English proficiency. A qualifying result in an English ' +
        'subject is sometimes accepted in place of a standardised test. ' +
        'Requirements differ by institution and by course — clinical courses are ' +
        'usually the strictest.',
      source: 'Confirm per-institution English requirements',
      verified: null,
    },

    {
      id: 'funding-not-recorded',
      domain: 'funding',
      title: 'Funding not recorded',
      // Off, not removed. The form no longer collects any funding information, so
      // `record.fundingSecured` is always undefined and this condition is now
      // permanently true. An enabled rule that fires on every record and says
      // "no funding arrangement has been recorded" is not advice, it is a
      // constant — and it would sit in every report. The coverage view shows it
      // as deliberately silent instead.
      enabled: false,
      when: 'record.fundingSecured !== true',
      advice:
        'No funding arrangement has been recorded. Scholarship deadlines usually ' +
        'fall earlier than admission deadlines, so funding deserves its own ' +
        'timeline rather than being left until an offer arrives.',
      source: 'internal',
      verified: '2026-01-01',
    },
    {
      id: 'funding-west-au',
      domain: 'funding',
      title: 'A Western Australian institution is among the choices',
      zhTitle: '志愿中有西澳的院校',
      when: 'anyInterestMatching("i.university", ["Western Australia", "UWA", "Curtin", "Murdoch", "Edith Cowan", "Notre Dame"])',
      advice:
        'Western Australia appears among your recorded choices: ' +
        '{{waUniversities}}. That state runs scholarship and bursary programmes of ' +
        'its own for international graduates of its school qualification. Amounts, ' +
        'quotas and eligibility change between rounds, so treat any figure you have ' +
        'heard as unconfirmed until you read the current programme page.',
      zh:
        '你记录的志愿里出现了西澳的院校：{{waUniversities}}。' +
        '该州有专门面向本州高中毕业国际生的奖学金与助学金项目。' +
        '金额、名额与资格每轮都会变，听到的任何数字都当作未确认，以当前项目页面为准。',
      source: 'Read the current state scholarship programme page',
      verified: '2026-09-25',
    },

    {
      id: 'perf-below-target',
      domain: 'performance',
      title: 'Current standing below stated target',
      when: 'record.targetAtar !== null && record.computedAtar !== null && record.computedAtar < record.targetAtar - T.targetGapPoints',
      advice:
        'Your current standing places you below your stated target of ' +
        '{{targetAtar}}. This is a gap to plan around, not a verdict. The ' +
        'practical question is whether the remaining assessments carry enough ' +
        'weight for the target to remain reachable — if they do not, adjusting ' +
        'the target now is better than discovering it at results release.',
      source: 'internal',
      verified: '2026-01-01',
    },
    {
      id: 'perf-subject-weak',
      domain: 'performance',
      title: 'A subject result is materially weak',
      when: 'anyScoreBelow(T.weakMark)',
      advice:
        'At least one subject result sits below {{weakMark}}. Before adding study ' +
        'hours everywhere, identify whether the weakness is content knowledge, exam ' +
        'technique, or time management — each needs a different fix. Reviewing ' +
        'marked scripts usually answers this faster than more revision does.',
      source: 'internal',
      verified: '2026-01-01',
    },
    {
      id: 'perf-high-at-load',
      domain: 'performance',
      title: 'Every recorded subject is an advanced-level subject',
      // Stays off, for a stronger reason than when it was merely unreachable.
      //
      // The condition counts subjects whose name begins with "AT" — the marker
      // the source workbook puts on ATAR courses — and compares that with the
      // number of subjects recorded. It used to read a "level" dropdown of intake
      // names, so it could never be true and the rule had never fired once.
      //
      // Now that the subject box is a pick-list of the ATAR subjects and nothing
      // else, the condition is true for EVERY record with four or more subjects.
      // The distinction it was written to warn about is enforced by the form
      // itself: a General subject cannot be recorded here, because a General mark
      // does not count toward an ATAR. Enabling it now would print "all of your
      // subjects are at the highest available level" on every complete report,
      // which is the same defect as funding-not-recorded: a constant presented as
      // advice. It is kept, switched off, so the coverage view records why.
      enabled: false,
      when: 'record.subjects.length >= T.subjectsForAggregate && countSubject("AT") === record.subjects.length',
      advice:
        'All {{subjectCount}} of your recorded subjects are at the highest ' +
        'available level. That is a demanding load, and the aggregate advantage ' +
        'only materialises if the marks hold up across all of them. Watch for ' +
        'one subject degrading to protect the others.',
      source: 'internal',
      verified: '2026-01-01',
    },

    {
      id: 'course-prereq-gap',
      domain: 'course',
      title: 'A stated prerequisite is not among the recorded subjects',
      when: 'anyInterestExpectationGap("i.field", record.subjects)',
      advice:
        'At least one of your chosen fields normally expects preparation you ' +
        'have not recorded. Requirements differ between institutions and ' +
        'between programmes inside one institution, so confirm the exact ' +
        'prerequisite for each course you are considering before assuming the ' +
        'gap is fatal — some accept a bridging unit instead.',
      source: 'Confirm the prerequisite for each specific programme',
      verified: null,
    },
    {
      id: 'course-prereq-optional-available',
      domain: 'course',
      title: 'An optional subject would strengthen the application',
      when: 'anyInterestOptionalGap("i.field", record.subjects)',
      advice:
        'For at least one of your fields, a subject that is not required but is ' +
        'commonly recommended is missing from your list. Recommended subjects ' +
        'rarely decide an offer on their own, but they reduce the chance of ' +
        'needing catch-up units in first year.',
      source: 'Confirm whether the recommendation applies at your target institutions',
      verified: null,
    },
    {
      id: 'atar-margin-thin',
      domain: 'performance',
      title: 'Standing is close to the nearest recorded minimum',
      // Re-based on the course library. It used to read a per-interest
      // `atarRequirement` that no control ever set, compared against a typed
      // estimate — two inputs that could not both exist, so the rule had never
      // fired. The library already knows the minimum for the country, field and
      // institution recorded, and `nearestAboveWithin` asks the one question
      // worth asking: is the nearest minimum you have not reached within reach?
      when: 'nearestAboveWithin(T.atarMarginPoints)',
      advice:
        'Your current standing sits within {{atarMarginPoints}} points of the ' +
        'nearest recorded minimum above you, {{nearestCourse}}. A margin that ' +
        'thin is the zone where a single assessment moves the outcome, so treat ' +
        'the next one as decisive rather than as practice.',
      source: 'internal',
      verified: '2026-01-01',
    },
    {
      id: 'atar-figure-not-recorded',
      domain: 'destination',
      title: 'The course library records no minimum for a stated choice',
      // The condition changed meaning, so the id is the only thing left of the
      // old rule. It used to test a per-interest figure the form never
      // collected, which made it true for every record with a choice: every
      // report told the reader to "record it" with nowhere to record it. What is
      // worth saying is the case that is actually actionable — the library holds
      // no course for the country, field and institution given, so no comparison
      // is possible and the reader has to look it up.
      when: 'anyInterestUnmatched()',
      advice:
        'The course library holds no course for at least one of your choices, ' +
        'so there is no recorded minimum to compare against. Either the ' +
        'combination is one this snapshot never covered, or the institution ' +
        'codes its entry differently — check the current course page, and treat ' +
        'this choice as unassessed rather than as met.',
      source: 'internal',
      verified: '2026-01-01',
    },
    /* ── prerequisites named by an actual course ───────────────────────────
     * The generic prereq rule above works from a field-level expectation table.
     * This one is narrower and stronger: it reads the subject names that the
     * institution's own requirement line states, so the gap it reports is the
     * one that course documents rather than one this project assumed. Only 8 of
     * the 54 recorded courses name a subject at all, which is why this reports
     * nothing for most fields — silence here is the honest answer, not a gap. */
    {
      id: 'course-prereq-named',
      domain: 'course',
      title: 'A recorded course names a subject you have not taken',
      when: 'anyNamedPrereqMissing()',
      advice:
        'Some courses recorded for your stated interest name a specific subject ' +
        'as a prerequisite, and your subject list does not include it: ' +
        '{{namedPrereqGaps}} This is the institution\'s own wording rather than a ' +
        'general expectation, so it is worth confirming on the course page before ' +
        'you change anything.',
      source: 'The requirement line on each institution course page',
      verified: '2026-09-25',
    },

    /* ── the skills and readiness module ───────────────────────────────────
     * Replaces the workbook's SKILLS ROADMAP sheet. It fires only when the
     * student has named a field, because a roadmap is per-field by construction;
     * with no field there is nothing specific and true to say, and a generic
     * paragraph would be filler. */
    {
      id: 'skills-roadmap',
      domain: 'skills',
      title: 'Careers, activities and skills for the stated field',
      when: 'roadmapFor()',
      advice:
        '{{roadmapField}} — what the work actually involves: {{roadmapCareers}} ' +
        'Beyond marks, these are what distinguish applicants: {{roadmapActivities}} ' +
        'Skills worth building deliberately: {{roadmapSkills}} {{roadmapWhy}}',
      source: 'internal',
      verified: '2026-01-01',
    },
    {
      id: 'skills-narrowness',
      domain: 'skills',
      title: 'A single narrow interest deserves a second option',
      when: 'record.interests.length === 1 && !!record.interests[0].field && record.interests[0].field !== "Undecided"',
      advice:
        'You have recorded one field of interest. That is not a problem, but a ' +
        'single narrow target is the plan most likely to need a fallback: ' +
        'admissions are decided by cohorts you cannot see, and a course that is ' +
        'reachable this year may not be next. Name one adjacent field you would ' +
        'also accept, and check that your subjects keep it open.',
      source: 'internal',
      verified: '2026-01-01',
    },
    {
      id: 'options-pathways',
      domain: 'destination',
      title: 'Routes that are not the direct degree',
      when: 'true',
      advice:
        'A direct degree entry is one route, not the only one. {{optionsList}} ' +
        'The reason to look now rather than in August is that these routes have ' +
        'their own deadlines, and several of them start earlier than the degree ' +
        'application does.',
      source: 'Verify each service page; links are entry points, not deadlines',
      verified: null,
    },
    {
      id: 'options-timeline',
      domain: 'destination',
      title: 'Application timelines for the stated destinations',
      when: 'timelineFor()',
      advice:
        '{{timelineList}} Deadlines move every cycle, so treat these as the ' +
        'shape of the year rather than the dates: the point is that the work ' +
        'starts well before the application does.',
      source: 'Verify dates on the official service each cycle',
      verified: null,
    },

    {
      id: 'atar-vs-recorded-minimum',
      domain: 'performance',
      title: 'Standing against the recorded minimums for the stated interests',
      zhTitle: '与所填方向已记录最低分的对照',
      when: 'anyReachableCourse()',
      advice:
        'Among the courses recorded for your stated interests, your current standing of ' +
        '{{standing}} reaches {{reachableCourse}}.{{#if nearestCourse}} The nearest one ' +
        'above you is {{nearestCourse}}, {{atarGap}} points away.{{/if}} Those minimums ' +
        'are a snapshot and move every intake, so treat them as a starting point.',
      zh:
        '在你填写方向的已记录课程里，你当前 {{standing}} 的水平够得上 {{reachableCourse}}。' +
        '{{#if nearestCourse}}最近的一门在你之上的是 {{nearestCourse}}，差 {{atarGap}} 分。{{/if}}' +
        '这些最低分是快照，每轮都会变，只作起点参考。',
      source: 'Verify the current minimum on the institution course page',
      verified: null,
    },
    {
      id: 'atar-below-all-recorded',
      domain: 'performance',
      title: 'Standing below every recorded minimum for the stated interests',
      zhTitle: '低于所填方向的全部已记录最低分',
      when: 'anyInterestHasCourses() && !anyReachableCourse()',
      advice:
        'Your current standing of {{standing}} does not reach any of the {{courseCount}} ' +
        'recorded minimums for your stated interests. The closest is {{nearestCourse}}, ' +
        '{{atarGap}} points above you. Better to know now, while there is still time to move ' +
        'either the target or the study plan.',
      zh:
        '你当前 {{standing}} 的水平，与你所填方向已记录的 {{courseCount}} 门课程最低分都还差一点。' +
        '最近的是 {{nearestCourse}}，高出 {{atarGap}} 分。' +
        '现在知道比成绩出来后再知道要好——无论是调整目标还是调整复习计划，都还来得及。',
      source: 'Verify the current minimum on the institution course page',
      verified: null,
    },

    {
      id: 'wellbeing-plan',
      domain: 'wellbeing',
      title: 'Standing study guidance',
      when: 'true',
      advice:
        'Two habits reliably separate students who hold their marks from those ' +
        'who lose them late: a written plan with dates rather than intentions, ' +
        'and practice under timed conditions rather than re-reading notes. ' +
        'Neither requires more hours than you are already spending.',
      source: 'internal',
      verified: '2026-01-01',
    },
    {
      id: 'wellbeing-overload',
      domain: 'wellbeing',
      title: 'Load may be excessive',
      when: 'record.subjects.length >= T.heavyLoadSubjects',
      advice:
        'You have recorded {{subjectCount}} subjects. At that load the usual ' +
        'failure mode is not laziness but cumulative fatigue, which shows up as ' +
        'declining accuracy in familiar material. Build recovery into the plan ' +
        'on purpose.',
      source: 'internal',
      verified: '2026-01-01',
    },
  ]

  /* --------------------------------------------------------------------------
   * 4. Assessment prioritisation matrix.
   *
   *    The original reduced every assessment to one advisory action via a
   *    two-dimensional lookup of importance against urgency. The mechanism is
   *    sound; the content choices below are original. Importance is derived
   *    automatically from the assessment's weight, so it cannot drift out of
   *    sync with the number it is based on.
   * ------------------------------------------------------------------------*/
  const importanceBands = [
    { max: 5, label: '1 — Trivial', level: 1 },
    { max: 10, label: '2 — Minor', level: 2 },
    { max: 15, label: '3 — Moderate', level: 3 },
    { max: 20, label: '4 — Major', level: 4 },
    { max: Infinity, label: '5 — Critical', level: 5 },
  ]

  // matrix[urgency][importance] — urgency 1 (low) .. 5 (critical).
  const matrix = {
    1: {
      1: 'Leave it; revisit only if time genuinely allows.',
      2: 'File the material for a short later pass.',
      3: 'Plan a short review in the coming weeks.',
      4: 'Schedule a focused session this week.',
      5: 'Plan a deep session; this carries real weight.',
    },
    2: {
      1: 'Skim only if the week stays clear.',
      2: 'Make a compact summary you can reuse.',
      3: 'Review tutorial material before the next topic lands.',
      4: 'Do practice questions, not just reading.',
      5: 'Book a block this week; do not leave it to chance.',
    },
    3: {
      1: 'Review only if something else falls through.',
      2: 'Short recap from your own notes.',
      3: 'Targeted review, then timed practice.',
      4: 'Begin practice papers under time pressure.',
      5: 'Start now — this one cannot be absorbed late.',
    },
    4: {
      1: 'Defer deliberately; it is not your bottleneck.',
      2: 'One focused hour, then reassess.',
      3: 'Prioritise over routine homework this week.',
      4: 'Do a full practice paper today.',
      5: 'Treat as urgent: revise and test yourself today.',
    },
    5: {
      1: 'Only if this is genuinely your lightest item.',
      2: 'Convert notes into a one-page recall sheet.',
      3: 'Prioritise over most other tasks immediately.',
      4: 'Full revision session within 48 hours.',
      5: 'Immediate, concentrated revision; attempt a mock now.',
    },
  }

  /* --------------------------------------------------------------------------
   * 5. ATAR <-> aggregate conversion.
   *
   *    HOW THIS WAS CALIBRATED, stated plainly so nobody has to guess.
   *
   *    The source workbook's TARGET CALCULATOR sheet states the relationship it
   *    uses as an expression over the sum of the best four subject marks:
   *
   *        ATAR = -135.443857026292
   *             + 5.0308281258900    * x
   *             - 0.0677052181977123 * x^2
   *             + 0.000468402019173927 * x^3
   *             - 1.64654759191973e-06 * x^4
   *             + 2.84286953057e-09    * x^5
   *             - 1.92463295e-12       * x^6
   *
   *    and its own worked example is an aggregate of 239.12838737245087 giving
   *    an ATAR of 80. These six numbers are the workbook's own coefficients,
   *    transcribed digit for digit — not a refit and not an independent
   *    calibration, and labelled that way rather than dressed up. They are
   *    checked twice: at load time against the reference the workbook states,
   *    and out of band by recalculating the workbook itself in a spreadsheet
   *    engine, which reproduced this evaluator at every aggregate tried.
   *
   *    WHAT WAS ACTUALLY CHECKED. The workbook's Historical data sheet holds 321
   *    students across three blocks; 272 of them also carry four or more subject
   *    marks, so an aggregate can be formed for them at all. Against those:
   *
   *      aggregate 105–200    74 students   mean error  +0.44, worst +12.42
   *      aggregate 200–373   198 students   mean error  -0.40, worst +13.30
   *
   *    93% of the 272 land within 5 ATAR points of their recorded outcome and 98%
   *    within 10. The curve is accurate across the range it is used in.
   *
   *    AN EARLIER VERSION OF THIS FILE CLAIMED THE OPPOSITE — that the curve ran
   *    +10.75 optimistic below ATAR 90, worsening to +34 in the bottom band — and
   *    the panel printed that as a warning under every figure below 90. The claim
   *    was an artefact of this project's own reader, not a property of the
   *    workbook. The sheet's cells are keyed by (column, row); that reader
   *    iterated rows once per column, so every subject mark arrived seven times.
   *    The top four of such a list is four copies of a student's single best
   *    subject, which is not an aggregate. The numbers above are what is left
   *    once each subject is counted once.
   *
   *    WHAT THIS MEANS FOR THE STUDENT. This is one institution's conversion for
   *    one intake. It is not an official ATAR statement. Every surface printing a
   *    number from this function prints the caveat with it, and `verifiedAgainst`
   *    records what was actually checked rather than claiming general validity.
   *
   *    `saneRange` is where the curve has been CHECKED, not where it is
   *    monotonic: it rises smoothly from 0 all the way to its turnover at
   *    aggregate 374.67, so monotonicity on its own would justify no floor at
   *    all. The floor is set by the data — the lowest best-four aggregate the
   *    workbook records is 105.8, a student who finished at ATAR 21.6, and the
   *    curve reads 22.35 there. Below that there is nothing to check against, so
   *    the conversion returns null rather than extrapolating. The ceiling is the
   *    turnover: a tool that reported "ATAR 97.85" for a perfect aggregate
   *    because of a curve artefact would be worse than one that says it cannot
   *    answer.
   *
   *    Model: atar = c0 + c1*x + ... over x = sum of the best N subject marks.
   * ------------------------------------------------------------------------*/
  const calibration = {
    label: 'Source workbook curve — one institution, one intake',
    verified: '2026-09-25',
    verifiedAgainst:
      'the workbook states aggregate 239.12838737245087 -> ATAR 80; this curve ' +
      'reproduces 80.00 there. Recalculated independently in a spreadsheet ' +
      'engine, which agreed at every aggregate tried, and measured against the ' +
      '272 students in the workbook who carry four or more marks',
    // Measured against every student the workbook records, not the convenient
    // ones. Keyed by AGGREGATE, because the aggregate is the input the curve
    // actually takes and the thing `saneRange` bounds. Kept as data so the panel
    // and the tests read the same numbers the README quotes, and so a future
    // re-measurement updates the prose by changing these rather than by editing
    // sentences.
    verifiedBands: [
      { from: 105, to: 200, students: 74, meanError: 0.44, worstError: 12.42,
        verdict: 'supported' },
      { from: 200, to: 373, students: 198, meanError: 0.40, worstError: 13.30,
        verdict: 'supported' },
    ],
    aggregateSize: 4,
    aggregateMax: 100,
    coefficients: [
      -135.443857026292,
      5.03082812589,
      -0.0677052181977123,
      0.000468402019173927,
      -1.64654759191973e-06,
      2.84286953057e-09,
      -1.92463295e-12,
    ],
    // Checked from 4x26.5 to 4x93.25 — the span the workbook's own students
    // cover. Below the floor nothing has been checked against, and above the
    // ceiling the curve turns over, so both are refused rather than clamped to a
    // wrong answer.
    saneRange: [105, 373],
    maxAtar: 99.95,
    clamp: [0, 99.95],
    // How many decimals each figure is printed to. Single-sourced here because
    // the panel and the written report had drifted apart on it.
    //
    // The aggregate keeps the precision of the marks that produced it: it is a
    // plain sum, and the source workbook prints 132.93 for the same four marks
    // this tool was printing as 132.9. The ATAR does NOT keep it. This curve's
    // measured error is a mean of 0.2 points and a worst case of 13, so
    // hundredths would claim a precision the conversion does not have — the
    // workbook shows one decimal for exactly that reason. One decimal is still
    // more than the conversion earns, but it is the figure the source states and
    // therefore the one a student can check this tool against.
    display: { aggregate: 2, atar: 1 },
    caveat:
      'One institution\'s conversion for one intake, taken from the source ' +
      'workbook. Not an official ATAR statement — treat it as an estimate and ' +
      'confirm against your own admissions centre.',
    // Printed under every figure, because it is true of every figure. The
    // workbook's curve is fitted to FINAL SCALED marks — the last column of its
    // own sheet — and a mark read off a school gradebook part-way through the
    // year is not one. The earlier version of this panel instead warned that the
    // curve ran ten points high below ATAR 90; that warning was wrong, and a
    // wrong warning is worse than none because it teaches the reader to discount
    // a number that was right.
    schoolMarkNote:
      'This converts whatever marks you enter as if they were your final ones. ' +
      'Marks read off a school gradebook mid-year are not final scaled marks, so ' +
      'read the figure as where this level of work finishes, not as a prediction.',
  }

  /* The curve is only usable if it is monotonic and reproduces the reference the
   * workbook states. Both are cheap to check and expensive to get wrong, so they
   * are checked on every load rather than trusted. A failure disables the
   * conversion instead of printing a wrong number. */
  const calibrationCheck = (function () {
    function f(x) {
      var v = 0
      for (var i = 0; i < calibration.coefficients.length; i++) {
        v += calibration.coefficients[i] * Math.pow(x, i)
      }
      return v
    }
    var problems = []
    var reference = f(239.12838737245087)
    if (Math.abs(reference - 80) > 0.01) {
      problems.push('reference aggregate gives ' + reference.toFixed(4) + ', expected 80')
    }
    var lo = calibration.saneRange[0]
    var hi = calibration.saneRange[1]
    var prev = f(lo)
    for (var x = lo + 1; x <= hi; x += 1) {
      var now = f(x)
      if (now < prev - 1e-9) {
        problems.push('curve is not monotonic at aggregate ' + x)
        break
      }
      prev = now
    }
    var top = f(hi)
    if (top < 90 || top > calibration.maxAtar + 0.001) {
      problems.push('top of range gives ' + top.toFixed(2) + ', expected near ' + calibration.maxAtar)
    }
    return { ok: problems.length === 0, problems: problems, reference: reference, top: top }
  })()

  /* --------------------------------------------------------------------------
   * 6. Public surface. The engine consumes only what is exported here.
   * ------------------------------------------------------------------------*/
  return {
    domains,
    vocabularies,
    rules,
    thresholds,
    capabilities,
    courseExpectations,
    importanceBands,
    matrix,
    calibration,
    calibrationCheck,
    meta: {
      title: 'AUSMAT Guide',
      subtitle: 'Rules-driven advising report',
      version: '2.0.0',
      contentPolicy:
        'All advice text in this file is original sample copy. All figures are ' +
        'placeholders pending verification against official sources.',
    },
  }
})()
