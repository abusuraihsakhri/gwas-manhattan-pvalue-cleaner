"use strict";
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const html = fs.readFileSync("web/index.html", "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(script, "Browser application script exists");
new vm.Script(script[1], {filename: "web/index.html"});

const elements = new Map();
const graphics = new Proxy({}, {get: (_, prop) => typeof prop === "string" ? () => {} : undefined});
const getElement = id => {
  if (!elements.has(id)) elements.set(id, {
    textContent: "", disabled: false, classList: {toggle() {}},
    getBoundingClientRect() {return {width: 850, height: 280}},
    getContext() {return graphics},
    addEventListener(event, callback) {this[event] = callback},
  });
  return elements.get(id);
};
const context = vm.createContext({
  document: {
    getElementById: getElement,
    createElement: () => ({click() {}, remove() {}}),
    body: {appendChild() {}},
  },
  window: {devicePixelRatio: 1, addEventListener() {}},
  console,
  URL: {createObjectURL: () => "blob:mock", revokeObjectURL() {}},
  Blob,
  setTimeout: callback => callback(),
});
vm.runInContext(script[1], context);
function evalIn(code) {return vm.runInContext(code, context)}

assert.equal(evalIn("parseCSV('CHR,BP,P,SNP\\n1,10,0.5,\"a,b\"\\n')[1][3]"), "a,b");
assert.ok(Math.abs(evalIn("normalInv(0.25)") + 0.67448975) < 1e-6);
evalIn("load('CHR,BP,P,SNP\\n1,10,0.5,rs1\\n2,20,1e-9,rs2\\nX,30,0,wrong\\n')");
assert.equal(evalIn("data.length"), 2);
assert.equal(getElement("valid").textContent, "2");
assert.equal(getElement("rejected").textContent, "1");
assert.equal(getElement("hits").textContent, "1");
assert.equal(getElement("download").disabled, false);
assert.equal(evalIn("csvCell('=1+1')"), "'=1+1");
assert.equal(evalIn("csvCell('-0.5')"), "-0.5");
assert.equal(evalIn("csvCell('-1+2')"), "'-1+2");
getElement("example").click();
assert.equal(evalIn("data.length"), 2640);
assert.ok(Number.isFinite(Number(getElement("lambda").textContent)));
evalIn("load('BAD,SCHEMA\\n1,2')");
assert.equal(getElement("download").disabled, true);
assert.equal(getElement("status").classList === undefined, false);
console.log("Browser JavaScript smoke tests passed");
