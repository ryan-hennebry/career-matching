// Behavioral unit test for getScoreTier — executes the function, not string matching.
// Run: node tests/test_get_score_tier.js

// Extract getScoreTier from components.js (module-level function)
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'public', 'js', 'components.js'), 'utf-8');
// Evaluate in isolated context to extract function
const vm = require('vm');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(src, ctx);

const assert = require('assert');
assert.strictEqual(ctx.getScoreTier(95), 'tier-high', '95 -> tier-high');
assert.strictEqual(ctx.getScoreTier(90), 'tier-high', '90 -> tier-high');
assert.strictEqual(ctx.getScoreTier(89), 'tier-mid', '89 -> tier-mid');
assert.strictEqual(ctx.getScoreTier(80), 'tier-mid', '80 -> tier-mid');
assert.strictEqual(ctx.getScoreTier(79), 'tier-low', '79 -> tier-low');
assert.strictEqual(ctx.getScoreTier(50), 'tier-low', '50 -> tier-low');
assert.strictEqual(ctx.getScoreTier(0), 'tier-low', '0 -> tier-low');
console.log('All getScoreTier tests passed.');
