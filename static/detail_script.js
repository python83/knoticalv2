document.addEventListener('DOMContentLoaded', () => {
    const habitDataElement = document.getElementById('habit-data');
    const habitId = habitDataElement.dataset.habitId;

    // DOM elements to update
    const habitNameElement = document.getElementById('habit-detail-name'); // Already set by Flask, but could update if needed
    const currentStreakElement = document.getElementById('current-streak');
    const bestStreakElement = document.getElementById('best-streak');
    const goalsMetElement = document.getElementById('goals-met');
    const calendarGridElement = document.getElementById('calendar-grid');
    const calendarMonthYearElement = document.getElementById('calendar-month-year');
    const prevMonthBtn = document.getElementById('prev-month');
    const nextMonthBtn = document.getElementById('next-month');


    let currentDisplayDate = new Date(); // Start with the current month
    let allCompletionDates = []; // Store all fetched dates

    // --- Functions ---

    const fetchHabitStats = async () => {
        if (!habitId) {
            console.error("Habit ID not found");
            return;
        }
        try {
            const response = await fetch(`/api/habits/${habitId}/stats`);
            if (!response.ok) {
                 throw new Error(`HTTP error! status: ${response.status}`);
            }
            const stats = await response.json();

            // Update streak info
            // habitNameElement.textContent = stats.name; // Optionally update if not set by Flask correctly
            currentStreakElement.textContent = stats.current_streak || 0;
            bestStreakElement.textContent = stats.best_streak || 0;
            goalsMetElement.textContent = stats.goals_met || 0; // Or total completions

            // Store completion dates and render initial calendar
            allCompletionDates = stats.completion_dates || [];
            renderCalendar(currentDisplayDate);

        } catch (error) {
            console.error("Failed to fetch habit stats:", error);
            // Display error to user?
            calendarGridElement.innerHTML = '<p style="color: red;">Error loading habit data.</p>';
        }
    };

    const renderCalendar = (dateToShow) => {
        calendarGridElement.innerHTML = ''; // Clear previous grid

        const year = dateToShow.getFullYear();
        const month = dateToShow.getMonth(); // 0-indexed (0 = Jan)
        const today = new Date();
        today.setHours(0,0,0,0); // Normalize today's date for comparison

        // Update month/year display
        calendarMonthYearElement.textContent = dateToShow.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });


        const firstDayOfMonth = new Date(year, month, 1);
        const lastDayOfMonth = new Date(year, month + 1, 0);
        const daysInMonth = lastDayOfMonth.getDate();
        const startDayOfWeek = firstDayOfMonth.getDay(); // 0=Sun, 1=Mon, ..., 6=Sat

        // Add empty cells for days before the 1st of the month
        for (let i = 0; i < startDayOfWeek; i++) {
            const emptyCell = document.createElement('div');
            emptyCell.classList.add('calendar-day', 'day-empty');
            calendarGridElement.appendChild(emptyCell);
        }

        // Add cells for each day of the month
        // Inside the renderCalendar loop...
        for (let day = 1; day <= daysInMonth; day++) {
            const cell = document.createElement('div');
            cell.classList.add('calendar-day');
            cell.textContent = day;

            const currentDate = new Date(year, month, day); // Creates local date at 00:00
            // No need for setHours here if only comparing date parts

            // --- CORRECT WAY TO GET LOCAL YYYY-MM-DD ---
            const currentYear = currentDate.getFullYear();
            const currentMonth = currentDate.getMonth() + 1; // Get month (0-11) -> (1-12)
            const currentDay = currentDate.getDate(); // Get day (1-31)

            // Pad month and day
            const currentMonthStr = String(currentMonth).padStart(2, '0');
            const currentDayStr = String(currentDay).padStart(2, '0');

            // This string represents the LOCAL calendar date
            const dateString = `${currentYear}-${currentMonthStr}-${currentDayStr}`;
            // --- END CORRECTION ---


            // Log for verification (optional now)
            // console.log(`Day: ${day}, Current Date Obj: ${currentDate.toString()}, Formatted Local String: ${dateString}`);


            // Check if this local date string is in the completion list
            if (allCompletionDates.includes(dateString)) {
                console.log(`   >>> CONDITION TRUE for ${dateString}. Adding class to element with text: [${cell.textContent}]`);
                cell.classList.add('day-completed');
                cell.title = "Completed!";
            }

            // Highlight today's date (compare using local dates)
            // Note: Need to format 'today' similarly for reliable comparison IF comparing strings
            // OR stick to comparing epoch time which is timezone independent AFTER normalizing hours
            const today = new Date();
            today.setHours(0, 0, 0, 0); // Normalize today for time comparison
            currentDate.setHours(0,0,0,0); // Normalize loop date as well

            if (currentDate.getTime() === today.getTime()) {
                console.log(`   >>> Adding day-today class to element with text: [${cell.textContent}]`);
                cell.classList.add('day-today');
            }

            calendarGridElement.appendChild(cell);
        }
    };

     // --- Event Listeners ---
     prevMonthBtn.onclick = () => {
         currentDisplayDate.setMonth(currentDisplayDate.getMonth() - 1);
         renderCalendar(currentDisplayDate);
     };

     nextMonthBtn.onclick = () => {
         currentDisplayDate.setMonth(currentDisplayDate.getMonth() + 1);
         renderCalendar(currentDisplayDate);
     };


    // --- Initial Load ---
    fetchHabitStats();
});