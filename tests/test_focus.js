const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const focusScript = fs.readFileSync(
  path.join(__dirname, "../src/static/focus.js"),
  "utf8"
);
const window = {};
vm.runInNewContext(focusScript, { window });

function createButton() {
  return { focusCalled: false, focus() { this.focusCalled = true; } };
}

function createActivityCard(name, buttons) {
  const heading = createButton();
  return {
    dataset: { activityName: name },
    querySelectorAll: () => buttons,
    querySelector: () => heading,
    heading,
  };
}

test("restores focus to the next participant at the removed position", () => {
  const buttons = [createButton(), createButton(), createButton()];
  const card = createActivityCard("Chess", buttons);
  const activitiesList = { children: [card] };

  window.restoreUnregisterFocus(activitiesList, "Chess", 1);

  assert.equal(buttons[1].focusCalled, true);
});

test("focuses the previous remaining participant when the removed one was last", () => {
  const buttons = [createButton(), createButton()];
  const card = createActivityCard("Chess", buttons);

  window.restoreUnregisterFocus({ children: [card] }, "Chess", 2);

  assert.equal(buttons[1].focusCalled, true);
});

test("focuses the activity heading when no participants remain", () => {
  const card = createActivityCard("Chess", []);

  window.restoreUnregisterFocus({ children: [card] }, "Chess", 0);

  assert.equal(card.heading.focusCalled, true);
});
