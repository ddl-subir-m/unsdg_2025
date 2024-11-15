// Team Phrase Generator Options
const phraseOptions = {
    actions: [
        "Dancing", "Flying", "Jumping", "Singing", "Racing",
        "Bouncing", "Skating", "Swimming", "Zooming", "Gliding",
        "Spinning", "Floating", "Marching", "Hopping", "Diving",
        "Blasting", "Dashing", "Rolling", "Surfing", "Leaping",
        "Painting", "Running", "Climbing", "Exploring", "Soaring"
    ],
    adjectives: [
        // Colors
        "Purple", "Golden", "Rainbow", "Silver", "Crimson",
        // Magic
        "Enchanted", "Magical", "Mystery", "Cosmic", "Sparkling",
        // Style
        "Glowing", "Shiny", "Neon", "Glittery", "Dazzling",
        // Nature
        "Wild", "Stormy", "Misty", "Sunny", "Tropical",
        // Power
        "Super", "Mighty", "Ultra", "Mega", "Powerful",
        // Fun
        "Silly", "Jolly", "Funky", "Wacky", "Happy"
    ],
    things: [
        // Animals
        "Elephants", "Dragons", "Penguins", "Tigers", "Dolphins",
        // Space
        "Rockets", "Stars", "Planets", "Comets", "Moons",
        // Nature
        "Trees", "Mountains", "Oceans", "Volcanoes", "Rainbows",
        // Food
        "Pizzas", "Tacos", "Sundaes", "Cookies", "Cupcakes",
        // Objects
        "Balloons", "Books", "Guitars", "Robots", "Crystals",
        // Fantasy
        "Wizards", "Unicorns", "Giants", "Heroes", "Ninjas"
    ]
};

// SDG Goals information
const sdgInfo = {
    1: { title: "No Poverty" },
    2: { title: "Zero Hunger" },
    3: { title: "Good Health" },
    4: { title: "Quality Education" },
    5: { title: "Gender Equality" },
    6: { title: "Clean Water" },
    7: { title: "Clean Energy" },
    8: { title: "Good Jobs" },
    9: { title: "Innovation" },
    10: { title: "Reduced Inequalities" },
    11: { title: "Sustainable Cities" },
    12: { title: "Responsible Consumption" },
    13: { title: "Climate Action" },
    14: { title: "Life Below Water" },
    15: { title: "Life On Land" },
    16: { title: "Peace & Justice" },
    17: { title: "Partnerships" }
};

document.addEventListener('DOMContentLoaded', function() {
    // Populate timezone dropdown
    const timezoneSelect = document.getElementById('timezone');
    if (timezoneSelect) {
        const timeZones = [
            "Pacific/Honolulu (GMT-10)",
            "America/Anchorage (GMT-9)",
            "America/Los_Angeles (GMT-8)",
            "America/Denver (GMT-7)",
            "America/Chicago (GMT-6)",
            "America/New_York (GMT-5)",
            "America/Halifax (GMT-4)",
            "America/St_Johns (GMT-3:30)",
            "America/Sao_Paulo (GMT-3)",
            "UTC (GMT)",
            "Europe/London (GMT)",
            "Europe/Paris (GMT+1)",
            "Europe/Helsinki (GMT+2)",
            "Asia/Dubai (GMT+4)",
            "Asia/Kolkata (GMT+5:30)",
            "Asia/Bangkok (GMT+7)",
            "Asia/Singapore (GMT+8)",
            "Asia/Tokyo (GMT+9)",
            "Australia/Sydney (GMT+10)",
            "Pacific/Auckland (GMT+12)"
        ];

        // Get user's timezone
        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        console.log('User timezone:', userTimezone);

        // Calculate offset for user's timezone
        const offset = new Date().getTimezoneOffset();
        const hours = Math.abs(Math.floor(offset / 60));
        const minutes = Math.abs(offset % 60);
        const sign = offset < 0 ? '+' : '-';
        const formattedOffset = `GMT${sign}${hours.toString().padStart(2, '0')}${minutes ? `:${minutes}` : ''}`;
        console.log('Formatted offset:', formattedOffset);

        // Create the user's timezone option
        const userTimezoneOption = `${userTimezone} (${formattedOffset})`;
        
        // Add user's timezone first
        timezoneSelect.innerHTML = `
            <option value="${userTimezone}" selected>${userTimezoneOption}</option>
        `;

        // Add other timezones
        timeZones.forEach(timezone => {
            const [zone, offset] = timezone.split(' ');
            if (zone !== userTimezone) {
                const option = new Option(timezone, zone);
                timezoneSelect.add(option);
            }
        });
    }

    // Team phrase generation
    const generatePhraseBtn = document.getElementById('generate_phrase_btn');
    const phrasePreview = document.getElementById('phrase_preview');
    const phraseText = document.getElementById('phrase_text');
    const copyPhraseBtn = document.getElementById('copy_phrase_btn');
    
    if (generatePhraseBtn && phrasePreview && copyPhraseBtn) {
        generatePhraseBtn.addEventListener('click', function() {
            const randomAction = phraseOptions.actions[Math.floor(Math.random() * phraseOptions.actions.length)];
            const randomAdjective = phraseOptions.adjectives[Math.floor(Math.random() * phraseOptions.adjectives.length)];
            const randomThing = phraseOptions.things[Math.floor(Math.random() * phraseOptions.things.length)];

            const phrase = `${randomAction} ${randomAdjective} ${randomThing}`;
            phraseText.textContent = phrase;
            phrasePreview.classList.remove('alert-info');
            phrasePreview.classList.add('alert-success');
            
            // Show copy button when phrase is generated
            copyPhraseBtn.style.display = 'block';
            
            // Add a hidden input to store the generated phrase
            let phraseInput = document.getElementById('team_phrase_input');
            if (!phraseInput) {
                phraseInput = document.createElement('input');
                phraseInput.type = 'hidden';
                phraseInput.id = 'team_phrase_input';
                phraseInput.name = 'team_phrase';
                generatePhraseBtn.parentNode.appendChild(phraseInput);
            }
            phraseInput.value = phrase;
        });

        // Update copy button success state
        copyPhraseBtn.addEventListener('click', function() {
            navigator.clipboard.writeText(phraseText.textContent).then(() => {
                const originalHTML = copyPhraseBtn.innerHTML;
                copyPhraseBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                copyPhraseBtn.classList.add('btn-success');
                copyPhraseBtn.classList.remove('btn-outline-pink');
                
                setTimeout(() => {
                    copyPhraseBtn.innerHTML = originalHTML;
                    copyPhraseBtn.classList.remove('btn-success');
                    copyPhraseBtn.classList.add('btn-outline-pink');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                alert('Failed to copy text. Please try again.');
            });
        });
    }

    // Team member management
    const maxMembers = 5;
    const membersContainer = document.getElementById('team_members_container');
    const addMemberBtn = document.getElementById('add_member_btn');

    if (addMemberBtn && membersContainer) {
        addMemberBtn.addEventListener('click', function() {
            const currentMembers = membersContainer.getElementsByClassName('member-input').length;
            if (currentMembers < maxMembers) {
                const memberDiv = document.createElement('div');
                memberDiv.className = 'member-input mb-2';
                memberDiv.innerHTML = `
                    <div class="input-group">
                        <input type="text" class="form-control" name="team_members[]" 
                               placeholder="Enter member name">
                        <button type="button" class="btn btn-outline-danger remove-member">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
                membersContainer.appendChild(memberDiv);

                if (currentMembers + 1 === maxMembers) {
                    addMemberBtn.disabled = true;
                }

                // Add remove functionality
                memberDiv.querySelector('.remove-member').addEventListener('click', function() {
                    memberDiv.remove();
                    addMemberBtn.disabled = false;
                });
            }
        });
    }

    // Date validation - prevent selecting past dates
    const dateInput = document.getElementById('date');
    if (dateInput) {
        // Get today's date in ISO format and extract just the date part
        const today = new Date().toISOString().split('T')[0];
        
        // Set the minimum date attribute
        dateInput.min = today;
        
        // Set default value to today
        dateInput.value = today;

        // Prevent manual entry of past dates
        dateInput.addEventListener('input', function(e) {
            const selectedDate = new Date(this.value + 'T00:00:00');
            const todayDate = new Date(today + 'T00:00:00');
            
            if (selectedDate < todayDate) {
                alert('Please select a future date');
                this.value = today;
            }
        });
    }

    // Time validation
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');

    if (startTimeInput && endTimeInput) {
        // Set default start time to next hour
        const now = new Date();
        now.setHours(now.getHours() + 1, 0, 0); // Next hour, 0 minutes
        startTimeInput.value = `${String(now.getHours()).padStart(2, '0')}:00`;
        
        // Set default end time to two hours from now
        const twoHoursLater = new Date(now);
        twoHoursLater.setHours(twoHoursLater.getHours() + 1);
        endTimeInput.value = `${String(twoHoursLater.getHours()).padStart(2, '0')}:00`;

        function validateTimes() {
            if (startTimeInput.value && endTimeInput.value) {
                const startParts = startTimeInput.value.split(':');
                const endParts = endTimeInput.value.split(':');
                
                const startHour = parseInt(startParts[0]);
                const startMinute = parseInt(startParts[1]);
                const endHour = parseInt(endParts[0]);
                const endMinute = parseInt(endParts[1]);

                if (endHour < startHour || (endHour === startHour && endMinute <= startMinute)) {
                    alert('End time must be after start time');
                    // Reset end time to one hour after start time
                    let newEndHour = startHour + 1;
                    if (newEndHour > 23) {
                        newEndHour = 23;
                        endTimeInput.value = `23:59`;
                    } else {
                        endTimeInput.value = `${String(newEndHour).padStart(2, '0')}:${String(startMinute).padStart(2, '0')}`;
                    }
                }
            }
        }

        // Add event listeners for both inputs
        startTimeInput.addEventListener('change', function() {
            validateTimes();
        });

        endTimeInput.addEventListener('change', function() {
            validateTimes();
        });

        // Also validate on form submission
        const form = startTimeInput.closest('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                validateTimes();
            });
        }
    }

    // Add event listener for description changes
    const descriptionInput = document.getElementById('description');
    const detectedSdgs = document.getElementById('detected_sdgs');
    const sdgBadges = document.getElementById('sdg_badges');
    const sdgDescriptions = document.getElementById('sdg_descriptions');
    const sdgGoalsInput = document.getElementById('sdg_goals');

    if (descriptionInput) {
        let typingTimer;
        const doneTypingInterval = 1000; // 1 second

        descriptionInput.addEventListener('input', function() {
            clearTimeout(typingTimer);
            const status = document.getElementById('sdg_detection_status');
            status.innerHTML = '<small><i class="fas fa-spinner fa-spin"></i> Analyzing description...</small>';

            typingTimer = setTimeout(function() {
                // This is where the AI detection will be integrated
                // For now, just show a placeholder message
                status.innerHTML = '<small><i class="fas fa-check-circle text-success"></i> Analysis complete</small>';
                detectedSdgs.classList.remove('d-none');
                
                // Placeholder: Show some example SDG goals
                // This will be replaced with actual AI detection
                const exampleGoals = [1, 3, 4];
                displayDetectedSDGs(exampleGoals);
            }, doneTypingInterval);
        });
    }

    function displayDetectedSDGs(goalNumbers) {
        // Clear previous results
        sdgBadges.innerHTML = '';
        
        // Display badges with goal number and title
        goalNumbers.forEach(num => {
            const goal = sdgInfo[num];
            
            // Create badge
            const badge = document.createElement('span');
            badge.className = 'sdg-badge';
            badge.textContent = `Goal ${num}: ${goal.title}`;
            sdgBadges.appendChild(badge);
        });

        // Store detected goals in hidden input
        sdgGoalsInput.value = goalNumbers.join(',');
    }
});
