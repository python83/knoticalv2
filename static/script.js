document.addEventListener('DOMContentLoaded', () => {
    const pendingList = document.getElementById('pending-habits');
    const doneTodayList = document.getElementById('done-today-habits');
    const doneThisWeekList = document.getElementById('done-this-week-habits');
    const notApplicableList = document.getElementById('not-applicable-today-habits');

    const pendingSection = document.getElementById('pending-section');
    const doneTodaySection = document.getElementById('done-today-section');
    const doneThisWeekSection = document.getElementById('done-this-week-section');
    const notApplicableSection = document.getElementById('not-applicable-section');


    const habitItemTemplate = document.getElementById('habit-item-template');
    const addHabitBtn = document.getElementById('add-habit-btn');
    const modal = document.getElementById('add-habit-modal');
    const closeModalBtn = modal.querySelector('.close-btn');
    const addHabitForm = document.getElementById('add-habit-form');

    // --- Functions ---

    const fetchHabits = async () => {
        try {
            const response = await fetch('/api/habits');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            // Clear existing lists
            pendingList.innerHTML = '';
            doneTodayList.innerHTML = '';
            doneThisWeekList.innerHTML = '';
            notApplicableList.innerHTML = '';


            // Populate lists
            populateList(pendingList, data.pending || [], 'pending');
            populateList(doneTodayList, data.done_today || [], 'done-today');
            populateList(doneThisWeekList, data.done_this_week || [], 'done-this-week');
            populateList(notApplicableList, data.not_applicable_today || [], 'not-applicable');

            // Show/hide sections based on content
            pendingSection.style.display = (data.pending && data.pending.length > 0) ? 'block' : 'none';
            doneTodaySection.style.display = (data.done_today && data.done_today.length > 0) ? 'block' : 'none';
            doneThisWeekSection.style.display = (data.done_this_week && data.done_this_week.length > 0) ? 'block' : 'none';
            notApplicableSection.style.display = (data.not_applicable_today && data.not_applicable_today.length > 0) ? 'block' : 'none';


        } catch (error) {
            console.error("Failed to fetch habits:", error);
            // Display error to user?
        }
    };

    const createHabitElement = (habit, status) => {
        const clone = habitItemTemplate.content.cloneNode(true);
        const listItem = clone.querySelector('.habit-item');
        const nameSpan = clone.querySelector('.habit-name');
        const completeBtn = clone.querySelector('.complete-btn');
        const deleteBtn = clone.querySelector('.delete-btn');

        listItem.dataset.habitId = habit.id; // Store ID on the element
        nameSpan.textContent = habit.name;

        // Add status class for styling
        if (status === 'done-today') {
             listItem.classList.add('done-today');
        } else if (status === 'done-this-week') {
            listItem.classList.add('done-this-week');
        } else if (status === 'pending') {
             listItem.classList.add('pending');
        }


        // Configure buttons based on status
        if (status !== 'pending') {
            completeBtn.style.display = 'none'; // Hide complete if not pending
        } else {
            completeBtn.style.display = 'inline-block';
            completeBtn.onclick = (e) => {
                 e.stopPropagation(); // Prevent li click event
                 completeHabit(habit.id, listItem);
            };
        }

         // Always show delete button
        deleteBtn.onclick = (e) => {
            e.stopPropagation(); // Prevent li click event
            deleteHabit(habit.id, listItem);
        };

        // Make the whole list item clickable for navigation
        listItem.onclick = () => {
            window.location.href = `/habit/${habit.id}`;
        };


        return clone; // Return the DocumentFragment
    };

    const populateList = (listElement, habits, status) => {
        if (habits && habits.length > 0) {
            habits.forEach(habit => {
                const habitElement = createHabitElement(habit, status);
                listElement.appendChild(habitElement);
            });
         }
    };

    const completeHabit = async (habitId, listItem) => {
         console.log(`Completing habit ${habitId}`);
        try {
            const response = await fetch(`/api/habits/${habitId}/complete`, {
                method: 'POST',
            });
            if (!response.ok) {
                 // Handle cases like already completed (maybe API returns 200 or 409)
                const errorData = await response.json().catch(() => ({})); // Avoid JSON parse error if no body
                 console.error(`Failed to complete habit ${habitId}: ${response.status}`, errorData);
                 alert(`Error: ${errorData.message || 'Could not complete habit.'}`);
                return;
            }
            // On success, refresh the list to show the item moved
             console.log(`Habit ${habitId} marked complete.`);
            fetchHabits();
        } catch (error) {
            console.error("Error completing habit:", error);
             alert('An error occurred while completing the habit.');
        }
    };

     const deleteHabit = async (habitId, listItem) => {
        if (!confirm(`Are you sure you want to delete the habit "${listItem.querySelector('.habit-name').textContent}"?`)) {
            return; // User cancelled
        }

        console.log(`Deleting habit ${habitId}`);
        try {
            const response = await fetch(`/api/habits/${habitId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({}));
                 console.error(`Failed to delete habit ${habitId}: ${response.status}`, errorData);
                 alert(`Error: ${errorData.message || 'Could not delete habit.'}`);
                 return;
            }
            // On success, remove the item visually or refresh the list
             console.log(`Habit ${habitId} deleted.`);
            listItem.remove(); // Optimistic UI update
             // Or uncomment below to refresh entire list from server
             // fetchHabits();
        } catch (error) {
            console.error("Error deleting habit:", error);
            alert('An error occurred while deleting the habit.');
        }
    };


    // --- Event Listeners ---

    // Show modal
    addHabitBtn.onclick = () => {
        modal.style.display = 'block';
    };

    // Hide modal
    closeModalBtn.onclick = () => {
        modal.style.display = 'none';
    };

    // Hide modal if clicking outside the content area
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };

    // Handle Add Habit Form Submission
    addHabitForm.onsubmit = async (event) => {
        event.preventDefault(); // Prevent page reload

        const nameInput = document.getElementById('habit-name');
        const frequencySelect = document.getElementById('habit-frequency');

        const habitData = {
            name: nameInput.value.trim(),
            frequency_type: frequencySelect.value
        };

        if (!habitData.name) {
            alert("Habit name cannot be empty.");
            return;
        }

        try {
            const response = await fetch('/api/habits', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(habitData),
            });

            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({}));
                 console.error(`Failed to add habit: ${response.status}`, errorData);
                 alert(`Error: ${errorData.message || 'Could not add habit.'}`);
                return;
            }

            // Success
            modal.style.display = 'none'; // Close modal
            addHabitForm.reset(); // Clear form
            fetchHabits(); // Refresh the list

        } catch (error) {
            console.error("Error adding habit:", error);
             alert('An error occurred while adding the habit.');
        }
    };


    // --- Initial Load ---
    fetchHabits();
});