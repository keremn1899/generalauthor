/**
 * Self-contained mock data for the World Design & Motion Lab.
 *
 * Provides realistic, typings-compliant world fixtures so every component
 * (tables, reader, canvas, ants, filters, derivations) can be tested,
 * inspected, and refined in isolation without requiring a live backend.
 */

import type { Docket, PassEntry } from "../api/construction";
import type {
  WorldAssertion,
  WorldDemand,
  WorldOverview,
  WorldReferent,
  WorldRelation,
} from "../api/world";
import type { Obligation } from "./FrontierTable";
import type { Directory } from "./WorldPage";
import type { FieldAssertion, WorkingSet } from "./workingSet";

export const MOCK_OVERVIEW: WorldOverview = {
  world_id: "bom-semantic-integration-c1",
  revision: 16298,
  relations: 20,
  referents: 3118,
  assertions: 8240,
  origins: {
    MECHANICAL: 6812,
    SEMANTIC: 217,
    DERIVED: 1211,
  },
  stale: [],
  incomplete: [],
  demand: {
    purpose: {
      id: "qualification_bottlenecks",
      revision: 1,
      statement: "Identify constraints preventing viability or leaving viability uncertain.",
    },
    obligations: 4,
    demanded: 4,
  },
};

export const MOCK_RELATIONS: WorldRelation[] = [
  {
    name: "acceptable_replacement",
    description: "Evaluated replacement candidate accepted under qualification rules.",
    mode: "BASE",
    arity: 3,
    referent_arity: 3,
    roles: [
      { name: "new_part", type: "REFERENT", referent: true, kinds: ["part"] },
      { name: "old_part", type: "REFERENT", referent: true, kinds: ["part"] },
      { name: "context", type: "REFERENT", referent: true, kinds: ["context"] },
    ],
    count: 24,
    stale: false,
    origins: ["ADJUDICATED"],
    completeness: null,
  },
  {
    name: "bom_item",
    description: "Items specified in the bill of materials.",
    mode: "BASE",
    arity: 1,
    referent_arity: 1,
    roles: [{ name: "bom_item", type: "REFERENT", referent: true, kinds: ["bom"] }],
    count: 400,
    stale: false,
    origins: ["MECHANICAL"],
    completeness: null,
  },
  {
    name: "candidate_replacement",
    description: "Parts identified as physical drop-in candidates.",
    mode: "BASE",
    arity: 2,
    referent_arity: 2,
    roles: [
      { name: "new_part", type: "REFERENT", referent: true, kinds: ["part"] },
      { name: "old_part", type: "REFERENT", referent: true, kinds: ["part"] },
    ],
    count: 208,
    stale: false,
    origins: ["SEMANTIC"],
    completeness: null,
  },
  {
    name: "deployment_environment",
    description: "Operational environments assigned to BOM assemblies.",
    mode: "BASE",
    arity: 2,
    referent_arity: 2,
    roles: [
      { name: "bom_item", type: "REFERENT", referent: true, kinds: ["bom"] },
      { name: "context", type: "REFERENT", referent: true, kinds: ["context"] },
    ],
    count: 400,
    stale: false,
    origins: ["MECHANICAL"],
    completeness: null,
  },
  {
    name: "eligible_part",
    description: "Parts verified as meeting voltage, temperature, and lifecycle requirements.",
    mode: "DERIVED",
    arity: 2,
    referent_arity: 2,
    roles: [
      { name: "part", type: "REFERENT", referent: true, kinds: ["part"] },
      { name: "bom_item", type: "REFERENT", referent: true, kinds: ["bom"] },
    ],
    count: 1211,
    stale: false,
    origins: ["DERIVED"],
    completeness: {
      status: "COMPLETE",
      universe: "bom_item",
      current: true,
      known_gaps: [],
    },
    derivation: {
      state: "SUCCEEDED",
      inputs: ["voltage_compatible", "temperature_compatible", "lifecycle"],
    },
  },
  {
    name: "lifecycle",
    description: "Manufacturer lifecycle status (active, NRND, EOL).",
    mode: "BASE",
    arity: 2,
    referent_arity: 1,
    roles: [
      { name: "part", type: "REFERENT", referent: true, kinds: ["part"] },
      { name: "status", type: "TEXT", referent: false },
    ],
    count: 1208,
    stale: false,
    origins: ["MECHANICAL"],
    completeness: null,
  },
  {
    name: "requires_temperature",
    description: "Operating temperature envelope demanded by BOM specification.",
    mode: "BASE",
    arity: 3,
    referent_arity: 1,
    roles: [
      { name: "bom_item", type: "REFERENT", referent: true, kinds: ["bom"] },
      { name: "minimum_c", type: "INTEGER", referent: false },
      { name: "maximum_c", type: "INTEGER", referent: false },
    ],
    count: 400,
    stale: false,
    origins: ["MECHANICAL"],
    completeness: null,
  },
  {
    name: "temperature_compatible",
    description: "Derived compatibility: part operating range covers BOM requirements.",
    mode: "DERIVED",
    arity: 2,
    referent_arity: 2,
    roles: [
      { name: "part", type: "REFERENT", referent: true, kinds: ["part"] },
      { name: "bom_item", type: "REFERENT", referent: true, kinds: ["bom"] },
    ],
    count: 1911,
    stale: false,
    origins: ["DERIVED"],
    completeness: {
      status: "COMPLETE",
      universe: "bom_item",
      current: true,
      known_gaps: [],
    },
    derivation: {
      state: "SUCCEEDED",
      inputs: ["part_type", "requires_temperature", "requires_type", "temperature_range"],
    },
  },
  {
    name: "voltage_compatible",
    description: "Derived compatibility: part rated voltage exceeds required operating voltage.",
    mode: "DERIVED",
    arity: 2,
    referent_arity: 2,
    roles: [
      { name: "part", type: "REFERENT", referent: true, kinds: ["part"] },
      { name: "bom_item", type: "REFERENT", referent: true, kinds: ["bom"] },
    ],
    count: 1512,
    stale: false,
    origins: ["DERIVED"],
    completeness: {
      status: "COMPLETE",
      universe: "bom_item",
      current: true,
      known_gaps: [],
    },
    derivation: {
      state: "SUCCEEDED",
      inputs: ["rated_voltage", "requires_voltage"],
    },
  },
];

export const MOCK_DIRECTORY: Directory = [
  { id: "bom:BOM-A", label: "Main logic controller BOM" },
  { id: "bom:BOM-B", label: "Power regulation assembly" },
  { id: "bom:BOM-C", label: "Sensor telemetry bridge" },
  { id: "bom:BOM-D", label: "High vibration cabinet" },
  { id: "part:C300", label: "Five-volt keyed connector" },
  { id: "part:R200", label: "Precision wirewound resistor" },
  { id: "part:R210", label: "Thick film surge resistor" },
  { id: "part:X100", label: "Field sensor interface" },
  { id: "part:X110", label: "Coated sensor interface" },
  { id: "part:X160", label: "Sealed outdoor transceiver" },
  { id: "context:high_vibration", label: "High vibration cabinet" },
  { id: "context:outdoor_enclosure", label: "Outdoor weather enclosure" },
];

export const MOCK_ASSERTION_DERIVED: WorldAssertion = {
  assertion_id: "assertion:temp_c300_bom_d",
  relation: "temperature_compatible",
  origin: "DERIVED",
  mode: "DERIVED",
  arity: 2,
  created_revision: 16298,
  assertion_state: "ASSERTED",
  relation_stale: false,
  completeness: {
    status: "COMPLETE",
    universe: "bom_item",
    current: true,
    known_gaps: [],
  },
  roles: [
    { name: "part", type: "REFERENT", referent: true, kinds: ["part"] },
    { name: "bom_item", type: "REFERENT", referent: true, kinds: ["bom"] },
  ],
  values: {
    part: "part:C300",
    bom_item: "bom:BOM-D",
  },
  derivation: {
    inputs: ["part_type", "requires_temperature", "requires_type", "temperature_range"],
  },
  grounding: [
    {
      kind: "WORLD",
      reference: "derivation:temperature_compatible:rev1",
      construction_method: "taskview_rule_compile",
    },
  ],
};

export const MOCK_ASSERTION_MECHANICAL: WorldAssertion = {
  assertion_id: "assertion:req_temp_bom_d",
  relation: "requires_temperature",
  origin: "MECHANICAL",
  mode: "BASE",
  arity: 3,
  created_revision: 13396,
  assertion_state: "ASSERTED",
  relation_stale: false,
  completeness: null,
  roles: [
    { name: "bom_item", type: "REFERENT", referent: true, kinds: ["bom"] },
    { name: "minimum_c", type: "INTEGER", referent: false },
    { name: "maximum_c", type: "INTEGER", referent: false },
  ],
  values: {
    bom_item: "bom:BOM-D",
    minimum_c: -10,
    maximum_c: 40,
  },
  grounding: [
    {
      kind: "SOURCE",
      reference: "source:engineering_spec_bom_d",
      native_handle: "bom_d_envelope.pdf",
      native_location: "Section 4.1 Table 2",
    },
  ],
};

export const MOCK_REFERENT: WorldReferent = {
  id: "part:C300",
  label: "Five-volt keyed connector",
  grounding: [
    {
      kind: "SOURCE",
      reference: "bom_c1_catalog",
      native_handle: "c1_catalog.csv",
      native_location: "row 402",
    },
  ],
  fields: [
    {
      relation: "lifecycle",
      role: "status",
      value: "active",
      assertion_id: "assertion:life_c300",
      origin: "MECHANICAL",
    },
    {
      relation: "rated_voltage",
      role: "volts",
      value: 12,
      assertion_id: "assertion:volt_c300",
      origin: "MECHANICAL",
    },
  ],
  relations: [
    {
      name: "temperature_compatible",
      arity: 2,
      mode: "DERIVED",
      stale: false,
      count: 14,
    },
    {
      name: "voltage_compatible",
      arity: 2,
      mode: "DERIVED",
      stale: false,
      count: 14,
    },
    {
      name: "eligible_part",
      arity: 2,
      mode: "DERIVED",
      stale: false,
      count: 12,
    },
  ],
};

export const MOCK_DEMAND: WorldDemand = {
  purpose: {
    id: "qualification_bottlenecks",
    revision: 1,
    statement: "Identify constraints preventing viability or leaving viability uncertain.",
  },
  rule: "Assembly must declare temperature tolerance window.",
  demanded: 4,
  obligations: [
    {
      relation: "acceptable_replacement",
      state: "UNRESOLVED",
      assertion_id: null,
      values: {
        new_part: "part:X110",
        old_part: "part:X160",
        context: "context:outdoor_enclosure",
      },
      demanded_by: { name: "qualification_bottlenecks", revision: 1 },
    },
    {
      relation: "requires_temperature",
      state: "ASSERTED",
      assertion_id: "assertion:req_temp_bom_d",
      values: {
        bom_item: "bom:BOM-D",
        minimum_c: -10,
        maximum_c: 40,
      },
      demanded_by: { name: "qualification_bottlenecks", revision: 1 },
    },
  ],
};

export const MOCK_OBLIGATION: Obligation = {
  key: "demand#0",
  relation: "acceptable_replacement",
  state: "UNRESOLVED",
  assertion_id: null,
  values: {
    new_part: "part:X110",
    old_part: "part:X160",
    context: "context:outdoor_enclosure",
  },
  demanded_by: { name: "qualification_bottlenecks", revision: 1 },
};

export function createMockWorkingSet(): WorkingSet {
  const referents = new Map([
    ["bom:BOM-D", { id: "bom:BOM-D", label: "BOM-D" }],
    ["part:C300", { id: "part:C300", label: "Five-volt keyed connector" }],
  ]);

  const assertions = new Map([
    [
      "assertion:req_temp_bom_d",
      {
        assertion_id: "assertion:req_temp_bom_d",
        relation: "requires_temperature",
        origin: "MECHANICAL",
        mode: "BASE",
        stale: false,
        completeness: null,
        spokes: [{ role: "bom_item", id: "bom:BOM-D" }],
        scalars: [
          { role: "minimum_c", value: -10 },
          { role: "maximum_c", value: 40 },
        ],
      },
    ],
  ]);

  const demands = new Map([
    [
      "demand#0",
      {
        key: "demand#0",
        relation: "acceptable_replacement",
        spokes: [
          { role: "new_part", id: "part:C300" },
          { role: "bom_item", id: "bom:BOM-D" },
        ],
        scalars: [],
      },
    ],
  ]);

  const bonds = [
    {
      assertion_id: "assertion:temp_c300_bom_d",
      relation: "temperature_compatible",
      origin: "DERIVED",
      mode: "DERIVED",
      stale: false,
      completeness: "COMPLETE" as const,
      source: "part:C300",
      target: "bom:BOM-D",
      spokes: [
        { role: "part", id: "part:C300" },
        { role: "bom_item", id: "bom:BOM-D" },
      ],
      scalars: [],
    },
  ];

  const positions = new Map([
    ["bom:BOM-D", { x: 500, y: 220 }],
    ["part:C300", { x: 500, y: 460 }],
    ["assertion:req_temp_bom_d", { x: 700, y: 220 }],
    ["demand#0", { x: 300, y: 340 }],
  ]);

  return { referents, assertions, demands, bonds, positions, expanded: new Set() };
}

/**
 * One mark of every construction origin, on a real field.
 *
 * The lab used to draw these by hand in SVG, and the copies had drifted: they
 * carried a corner radius the product does not have, and the ants specimens
 * had grown their own dash arithmetic instead of the bead count `SelectionAnts`
 * locks to graph-space path length. Both galleries now render through
 * `WorldCanvas`, which means what you inspect is what ships — including the
 * geometry rule the whole read side rests on, that construction origin is
 * carried by shape and never by colour.
 *
 * Laid out left to right in the order a reader meets them: what the machine
 * compiled, what it judged, what a person adjudicated, what was derived, and
 * what nobody has decided.
 */
export function createSpecimenSet(): WorkingSet {
  const referents = new Map([
    ["bom:BOM-D", { id: "bom:BOM-D", label: "BOM-D" }],
    ["part:C300", { id: "part:C300", label: "Five-volt keyed connector" }],
    ["part:C301", { id: "part:C301", label: "Twelve-volt keyed connector" }],
  ]);

  const plate = (
    id: string,
    relation: string,
    origin: string,
    mode: string,
    spokes: { role: string; id: string }[],
  ): [string, FieldAssertion] => [
    id,
    {
      assertion_id: id,
      relation,
      origin,
      mode,
      stale: false,
      completeness: null,
      spokes,
      scalars: [{ role: "minimum_c", value: -10 }],
    },
  ];

  const assertions = new Map([
    // Knockout: the plate is the field exactly, and the filament under it
    // stops being read rather than being covered.
    plate("specimen:mechanical", "requires_temperature", "MECHANICAL", "BASE", [
      { role: "bom_item", id: "bom:BOM-D" },
    ]),
    // Filled ink: the machine's own judgment, not a compile.
    plate("specimen:semantic", "candidate_replacement", "SEMANTIC", "BASE", [
      { role: "new_part", id: "part:C300" },
    ]),
    // Filled, with the crown: a person's verdict standing over the machine's.
    plate("specimen:adjudicated", "acceptable_replacement", "ADJUDICATED", "BASE", [
      { role: "new_part", id: "part:C301" },
    ]),
    // Outlined, with the shelf it rests on.
    plate("specimen:derived", "eligible_part", "DERIVED", "DERIVED", [
      { role: "part", id: "part:C300" },
    ]),
  ]);

  // Hollow and dotted. Not a weaker assertion — the absence of one.
  const demands = new Map([
    [
      "demand#specimen",
      {
        key: "demand#specimen",
        relation: "viable_replacement",
        spokes: [
          { role: "new_part", id: "part:C301" },
          { role: "old_part", id: "part:C300" },
        ],
        scalars: [],
      },
    ],
  ]);

  // The third ant geometry: a bond is the filament itself, trimmed clear of
  // the discs at each end.
  const bonds = [
    {
      assertion_id: "specimen:bond",
      relation: "temperature_compatible",
      origin: "DERIVED",
      mode: "DERIVED",
      stale: false,
      completeness: "COMPLETE" as const,
      source: "part:C300",
      target: "bom:BOM-D",
      spokes: [
        { role: "part", id: "part:C300" },
        { role: "bom_item", id: "bom:BOM-D" },
      ],
      scalars: [],
    },
  ];

  const positions = new Map([
    ["bom:BOM-D", { x: 160, y: 120 }],
    ["part:C300", { x: 160, y: 400 }],
    ["part:C301", { x: 760, y: 400 }],
    ["specimen:mechanical", { x: 160, y: 260 }],
    ["specimen:semantic", { x: 400, y: 400 }],
    ["specimen:adjudicated", { x: 620, y: 260 }],
    ["specimen:derived", { x: 400, y: 120 }],
    ["demand#specimen", { x: 760, y: 120 }],
  ]);

  return { referents, assertions, demands, bonds, positions, expanded: new Set() };
}

/**
 * The constructor's nine passes, in every state the spine can draw.
 *
 * The spine encodes state as *geometry* — filled, half, dashed, struck across,
 * struck down, dotted, bare — so a gallery that showed only the happy run
 * would be showing a seventh of the vocabulary. Two of the seven are the
 * important ones. `null` with no check is "no scorer has spoken", which the
 * surface reports rather than filling in, because a front end that inferred
 * certification would be certifying passes. `null` with a refused check is P1
 * saying the purpose's required consumer fields are not declarable — the pass
 * wrote its artifact and objected to it in the same breath, and a rail that
 * drew that as unscored would be hiding the objection behind an absence.
 */
export const MOCK_PASSES: PassEntry[] = [
  { pass: "p0", artifact: "00_intention_contract.json", present: true, ran: true, scored: null, seconds: null, question: "", agent: null, state: "CERTIFIED", because: [], attestations: [] },
  { pass: "p1", artifact: "01_vocabulary.json", present: true, ran: true, scored: null, seconds: null, question: "", agent: null, state: null, because: ["its own check 01_abi_completeness.json says no — unsatisfied: contract_id"], attestations: [{ artifact: "01_abi_completeness.json", ok: false, says: ["unsatisfied: contract_id"] }] },
  { pass: "p2", artifact: "02_mechanical_world/", present: true, ran: true, scored: null, seconds: null, question: "", agent: null, state: "PROVISIONAL", because: ["an input moved under it"], attestations: [] },
  { pass: "p3", artifact: "03_obligations.json", present: true, ran: true, scored: null, seconds: null, question: "", agent: null, state: "CERTIFIED", because: [], attestations: [] },
  { pass: "p4", artifact: "04_packets/", present: true, ran: true, scored: null, seconds: null, question: "", agent: null, state: "STALE", because: ["an intervention stands upstream"], attestations: [] },
  { pass: "p5", artifact: "05_dispositions.json", present: true, ran: true, scored: null, seconds: null, question: "", agent: null, state: null, because: ["no scorer has spoken"], attestations: [] },
  { pass: "p6", artifact: "06_admission.json", present: true, ran: true, scored: null, seconds: null, question: "", agent: null, state: "FAILED", because: ["the artifact is absent"], attestations: [{ artifact: "06_provenance.json", ok: true, says: [] }] },
  { pass: "p7", artifact: "07_derivations.json", present: false, ran: false, scored: null, seconds: null, question: "", agent: null, state: null, because: [], attestations: [] },
  { pass: "p8", artifact: "08_outputs/", present: false, ran: false, scored: null, seconds: null, question: "", agent: null, state: null, because: [], attestations: [] },
];

/**
 * A docket with one row of each kind, because the docket's whole job is telling
 * three states apart: a machine judgment standing, a human verdict superseding
 * one, and a question nobody has answered. The blocking row is the only one
 * whose status colour changes under a person, so it is the row you tune.
 */
export const MOCK_DOCKET: Docket = {
  counts: { total: 4, open: 2, decided: 2, blocking: 1 },
  obligations: [
    {
      obligation_id: "ob:temp_c300_bom_d",
      relation: "temperature_compatible",
      values: { new_part: "C300", old_part: "BOM-D" },
      why_demanded: "purpose (a) cannot answer without a temperature verdict",
      required_by: ["a"],
      state: "decided",
      disposition: "HOLDS",
      rationale: "datasheet range covers the stated envelope",
      verification: "packet 04/ob:temp_c300_bom_d",
      observations: 3,
      known_missing_information: null,
      verdict: null,
      open: false,
      blocks: { purposes: ["a"], relations: ["acceptable_replacement"], blocking: false },
    },
    {
      obligation_id: "ob:temp_c301_bom_d",
      relation: "temperature_compatible",
      values: { new_part: "C301", old_part: "BOM-D" },
      why_demanded: "purpose (a) cannot answer without a temperature verdict",
      required_by: ["a"],
      state: "decided",
      disposition: "FAILS",
      rationale: "upper bound is 5°C short of the envelope",
      verification: "packet 04/ob:temp_c301_bom_d",
      observations: 2,
      known_missing_information: null,
      verdict: {
        kind: "ADJUDICATION",
        obligation_id: "ob:temp_c301_bom_d",
        disposition: "HOLDS",
        support_claim: "derating curve applies; the envelope is transient",
        supersedes: "FAILS",
        actor: "j.mercer",
        at: "2026-08-31T09:14:00Z",
      },
      open: false,
      blocks: { purposes: ["a"], relations: ["acceptable_replacement"], blocking: false },
    },
    {
      obligation_id: "ob:pkg_c302_bom_e",
      relation: "package_compatible",
      values: { new_part: "C302", old_part: "BOM-E" },
      why_demanded: "purpose (b) needs a footprint decision",
      required_by: ["b"],
      state: null,
      disposition: null,
      rationale: null,
      verification: null,
      observations: 0,
      known_missing_information: "no footprint drawing in the packet",
      verdict: null,
      open: true,
      blocks: { purposes: ["b"], relations: [], blocking: false },
    },
    {
      obligation_id: "ob:supply_c303",
      relation: "second_source_exists",
      values: { part: "C303" },
      why_demanded: "purpose (c) answers nothing while this is open",
      required_by: ["c"],
      state: null,
      disposition: null,
      rationale: null,
      verification: null,
      observations: 1,
      known_missing_information: null,
      verdict: null,
      open: true,
      blocks: { purposes: ["c"], relations: ["acceptable_replacement"], blocking: true },
    },
  ],
};
