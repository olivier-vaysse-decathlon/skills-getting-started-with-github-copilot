window.restoreUnregisterFocus = (activitiesList, activityName, participantIndex) => {
  const activityCard = Array.from(activitiesList.children).find(
    (card) => card.dataset.activityName === activityName
  );
  if (!activityCard) {
    return;
  }

  const removeButtons = activityCard.querySelectorAll(".remove-participant");
  const focusTarget =
    removeButtons[Math.min(participantIndex, removeButtons.length - 1)] ||
    activityCard.querySelector("h4");
  focusTarget?.focus();
};
