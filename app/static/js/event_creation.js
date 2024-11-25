const createTeamBtn = document.getElementById('create_team_btn');
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const elements = {
        // Team related elements
        teamChoiceInput: document.getElementById('team_choice'),
        existingTeamTab: document.getElementById('existing-team-tab'),
        newTeamTab: document.getElementById('new-team-tab'),
        selectedTeamIdInput: document.getElementById('selected_team_id'),
        teamPhraseInput: document.getElementById('team_phrase'),
        eventForm: document.getElementById('event_form'),
        createTeamBtn: document.getElementById('create_team_btn'),

        
        // Team search elements
        teamSearch: document.getElementById('team_search'),
        teamSearchResults: document.getElementById('team_search_results'),
        selectedTeamName: document.getElementById('selected_team_name'),

        
        // Phrase generation elements
        generatePhraseBtn: document.getElementById('generate_phrase_btn'),
        phraseText: document.getElementById('phrase_text'),
        copyPhraseBtn: document.getElementById('copy_phrase_btn'),
        
        // Time inputs
        startTimeInput: document.getElementById('start_time'),
        endTimeInput: document.getElementById('end_time'),
        
        // Password visibility toggle
        togglePhraseVisibility: document.getElementById('toggle_phrase_visibility'),
    };

    // Initialize team choice
    if (elements.teamChoiceInput) {
        elements.teamChoiceInput.value = 'existing';
    }

    // Team tab handling
    if (elements.existingTeamTab && elements.teamChoiceInput) {
        elements.existingTeamTab.addEventListener('click', () => {
            elements.teamChoiceInput.value = 'existing';
        });
    }

    if (elements.newTeamTab && elements.teamChoiceInput) {
        elements.newTeamTab.addEventListener('click', () => {
            elements.teamChoiceInput.value = 'new';
        });
    }

    // Team search functionality
    if (elements.teamSearch && elements.teamSearchResults) {
        elements.teamSearch.addEventListener('input', debounce(async function() {
            const searchTerm = elements.teamSearch.value;
            if (searchTerm && searchTerm.trim().length >= 2) {
                try {
                    const response = await fetch(`/api/search_teams?q=${encodeURIComponent(searchTerm.trim())}`);
                    const teams = await response.json();
                    
                    // Clear previous results
                    elements.teamSearchResults.innerHTML = '';
                    
                    if (teams.length === 0) {
                        elements.teamSearchResults.innerHTML = `
                            <div class="list-group-item text-muted">
                                No teams found
                            </div>
                        `;
                        return;
                    }

                    // Display results and add click handlers
                    teams.forEach(team => {
                        // Separate captain and other members
                        const captain = team.captain;
                        const otherMembers = team.members.filter(member => member !== captain);
                        
                        // Combine captain and other members with proper formatting
                        const membersList = [
                            `<strong>${captain} (Captain)</strong>`,
                            ...otherMembers
                        ].join(', ');

                        const teamElement = document.createElement('div');
                        teamElement.className = 'list-group-item list-group-item-action';
                        teamElement.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center">
                                <strong>${team.name}</strong>
                                <small>${team.member_count} members</small>
                            </div>
                            <div class="text-muted small">
                                <i class="fas fa-users me-1"></i> ${membersList}
                            </div>
                        `;

                        // Add click handler for team selection
                        teamElement.addEventListener('click', () => {
                            // Update hidden inputs
                            document.getElementById('selected_team_id').value = team.id;
                            
                            // Update search input to show selected team
                            elements.teamSearch.value = team.name;
                            
                            // Clear search results
                            elements.teamSearchResults.innerHTML = '';
                        });

                        elements.teamSearchResults.appendChild(teamElement);
                    });
                } catch (error) {
                    console.error('Error searching teams:', error);
                    elements.teamSearchResults.innerHTML = `
                        <div class="list-group-item text-danger">
                            Error searching teams
                        </div>
                    `;
                }
            } else {
                elements.teamSearchResults.innerHTML = '';
            }
        }, 300));
    }

    // Team selection function
    function selectTeam(team) {
        if (elements.selectedTeamIdInput && elements.selectedTeamName && elements.existingTeamVerify) {
            document.getElementById('selected_team_id').value = team.id;
            elements.selectedTeamName.textContent = team.name;
            elements.existingTeamVerify.style.display = 'block';
            elements.teamSearch.value = team.name;
            elements.teamSearchResults.innerHTML = '';
            
            console.log('Selected team ID:', document.getElementById('selected_team_id').value);
        }
    }

    // Check if we have a selected team from a previous submission
    if (window.selectedTeam) {
        // Set the team information
        elements.selectedTeamIdInput.value = window.selectedTeam.id;
        elements.teamSearch.value = window.selectedTeam.name;
        
        // Make sure the "Select Team" tab is active
        document.getElementById('existing-team-tab').click();

    }

    // Phrase generation
    if (elements.generatePhraseBtn && elements.phraseText && elements.copyPhraseBtn) {
        const phraseOptions = {
            actions: ['Build', 'Create', 'Design', 'Develop', 'Establish', 'Form', 'Generate', 'Implement', 'Launch', 'Make'],
            adjectives: ['Better', 'Brighter', 'Cleaner', 'Greater', 'Greener', 'Healthier', 'Newer', 'Safer', 'Smarter', 'Stronger'],
            things: ['Communities', 'Futures', 'Homes', 'Lives', 'Neighborhoods', 'Places', 'Spaces', 'Systems', 'Tomorrows', 'Worlds']
        };

        elements.generatePhraseBtn.addEventListener('click', function() {
            const randomAction = phraseOptions.actions[Math.floor(Math.random() * phraseOptions.actions.length)];
            const randomAdjective = phraseOptions.adjectives[Math.floor(Math.random() * phraseOptions.adjectives.length)];
            const randomThing = phraseOptions.things[Math.floor(Math.random() * phraseOptions.things.length)];

            const phrase = `${randomAction} ${randomAdjective} ${randomThing}`;
            elements.phraseText.textContent = phrase;
            elements.copyPhraseBtn.style.display = 'block';
        });

        // Copy button functionality
        elements.copyPhraseBtn.addEventListener('click', async function() {
            try {
                const phraseText = elements.phraseText.textContent.split('\n')[0].trim();
                await navigator.clipboard.writeText(phraseText);
                
                const originalHTML = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                this.classList.add('btn-success');
                this.classList.remove('btn-outline-pink');
                
                setTimeout(() => {
                    this.innerHTML = originalHTML;
                    this.classList.remove('btn-success');
                    this.classList.add('btn-outline-pink');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy text: ', err);
                alert('Failed to copy text. Please try again.');
            }
        });
    }

    // Time validation
    if (elements.startTimeInput && elements.endTimeInput) {
        function validateTimes() {
            if (elements.startTimeInput.value && elements.endTimeInput.value) {
                const startTime = elements.startTimeInput.value;
                const endTime = elements.endTimeInput.value;

                if (endTime <= startTime) {
                    showFlashMessage('End time must be after start time', 'warning');
                    // Reset end time to one hour after start time
                    const [hours, minutes] = startTime.split(':');
                    let newHour = parseInt(hours) + 1;
                    if (newHour > 23) newHour = 23;
                    elements.endTimeInput.value = `${String(newHour).padStart(2, '0')}:${minutes}`;
                }
            }
        }

        elements.startTimeInput.addEventListener('change', validateTimes);
        elements.endTimeInput.addEventListener('change', validateTimes);
    }

    // Add this function to populate timezone dropdown
    function populateTimezoneDropdown() {
        const timezoneSelect = document.getElementById('timezone');
        if (!timezoneSelect) return;

        // Get user's timezone
        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        
        // Get all timezone names
        const timeZones = moment.tz.names();

        // Clear existing options
        timezoneSelect.innerHTML = '';
        
        timeZones.forEach(zone => {
            const option = document.createElement('option');
            option.value = zone;
            option.text = `${zone} (${moment.tz(zone).format('Z')})`;
            option.selected = zone === userTimezone;
            timezoneSelect.appendChild(option);
        });
    }

    // Call this when the document loads
    populateTimezoneDropdown();

    // Add this event listener
    document.getElementById('event_form').addEventListener('submit', function(e) {
        const teamId = document.getElementById('selected_team_id').value;
        if (!teamId) {
            e.preventDefault();
            showFlashMessage('Please select a team before creating an event', 'warning');
        }
    });

    const addMemberBtn = document.getElementById('add_member_btn');
    const membersContainer = document.getElementById('team_members_container');
    const MAX_MEMBERS = 30;

    if (addMemberBtn && membersContainer) {
        addMemberBtn.addEventListener('click', function() {
            const currentMembers = membersContainer.getElementsByClassName('member-input');
            
            if (currentMembers.length >= MAX_MEMBERS) {
                showFlashMessage('Maximum 30 team members allowed', 'warning');
                return;
            }

            const newMemberDiv = document.createElement('div');
            newMemberDiv.className = 'member-input mb-2';
            newMemberDiv.innerHTML = `
                <div class="input-group">
                    <input type="text" 
                           class="form-control" 
                           name="team_members[]" 
                           placeholder="Enter member name">
                    <button type="button" 
                            class="btn btn-outline-danger remove-member"
                            onclick="this.closest('.member-input').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;

            membersContainer.appendChild(newMemberDiv);
        });
    }

    
    if (createTeamBtn) {
        createTeamBtn.addEventListener('click', async function() {
            // Get team details
            const teamName = document.getElementById('team_name').value.trim();
            const teamPhrase = document.getElementById('phrase_text').textContent.trim();
            const memberInputs = document.querySelectorAll('input[name="team_members[]"]');
            const teamMembers = Array.from(memberInputs)
                                   .map(input => input.value.trim())
                                   .filter(value => value !== '');

            // Validate inputs
            if (!teamName) {
                showFlashMessage('Please enter a team name', 'warning');
                return;
            }

            if (!teamMembers.length) {
                showFlashMessage('Please add at least one team member', 'warning');
                return;
            }

            if (teamPhrase === 'Click the button to generate your team phrase') {
                showFlashMessage('Please generate a team phrase', 'warning');
                return;
            }

            try {
                const response = await fetch('/api/create_team', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: teamName,
                        team_phrase: teamPhrase,
                        members: teamMembers
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    // Update the form with the new team's information
                    document.getElementById('team_choice').value = 'existing';
                    document.getElementById('selected_team_id').value = data.team_id;
                    document.getElementById('team_phrase').value = teamPhrase;
                    
                    // Show success message
                    showFlashMessage('Team created successfully!', 'success');
                    
                    
                    // Switch to the existing team tab and show the selected team
                    document.getElementById('existing-team-tab').click();
                    document.getElementById('team_search').value = teamName;
                } else {
                    showFlashMessage(data.message || 'Failed to create team', 'danger');
                }
            } catch (error) {
                console.error('Error:', error);
                showFlashMessage('An error occurred while creating the team', 'danger');
            }
        });
    }

    // Add this after the timezone population code (around line 235)
    const descriptionInput = document.getElementById('description');
    const sdgDetectionStatus = document.getElementById('sdg_detection_status');
    const detectedSdgs = document.getElementById('detected_sdgs');
    const sdgBadges = document.getElementById('sdg_badges');

    if (descriptionInput) {
        let typingTimer;
        const doneTypingInterval = 1000;

        descriptionInput.addEventListener('keyup', () => {
            clearTimeout(typingTimer);
            if (descriptionInput.value.trim()) {
                sdgDetectionStatus.innerHTML = '<small><i class="fas fa-spinner fa-spin"></i> Analyzing description...</small>';
                typingTimer = setTimeout(detectSdgs, doneTypingInterval);
            } else {
                // Clear SDG badges and reset status when description is empty
                sdgDetectionStatus.innerHTML = '<small><i class="fas fa-info-circle"></i> SDG goals will be automatically detected from your event description</small>';
                detectedSdgs.classList.add('d-none');
                sdgBadges.innerHTML = '';
                document.getElementById('sdg_goals').value = '';
            }
        });

        async function detectSdgs() {
            const description = descriptionInput.value;
            if (!description.trim()) return;

            try {
                const response = await fetch('/api/analyze_sdgs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ description })
                });

                const data = await response.json();
                
                if (response.ok) {
                    sdgDetectionStatus.innerHTML = '<small><i class="fas fa-check text-success"></i> SDG goals detected</small>';
                    detectedSdgs.classList.remove('d-none');
                    
                    // Update badges with remove buttons
                    sdgBadges.innerHTML = data.goals.map(goal => `
                        <span class="badge ${goal === data.primary ? 'bg-primary' : 'bg-secondary'} me-1 mb-1">
                            SDG ${goal}: ${window.SDG_DESCRIPTIONS[goal]}
                            <button type="button" class="btn-close btn-close-white ms-2" 
                                    aria-label="Remove" 
                                    onclick="removeSDGBadge(this, ${goal}, ${goal === data.primary})">
                            </button>
                        </span>
                    `).join('');
                    
                    // Update hidden input
                    document.getElementById('sdg_goals').value = JSON.stringify(data);
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                console.error('Error:', error);
                sdgDetectionStatus.innerHTML = '<small><i class="fas fa-exclamation-circle text-danger"></i> Error detecting SDGs</small>';
            }
        }
    }
});

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add this function at the start of your file
async function showFlashMessage(message, category) {
    const flashContainer = document.querySelector('.flash-messages');
    if (flashContainer) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${category} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        flashContainer.appendChild(alert);
    }
}

// Add this function outside the existing event listeners
function removeSDGBadge(button, goalToRemove, isPrimary) {
    const badge = button.parentElement;
    const sdgGoalsInput = document.getElementById('sdg_goals');
    
    // Get current SDG goals data
    let currentData = JSON.parse(sdgGoalsInput.value);
    
    // Remove the goal from the array
    currentData.goals = currentData.goals.filter(goal => goal !== goalToRemove);
    
    // If we removed the primary goal and there are other goals left,
    // make the first remaining goal the primary
    if (isPrimary && currentData.goals.length > 0) {
        currentData.primary = currentData.goals[0];
    } else if (currentData.goals.length === 0) {
        // If no goals left, reset primary to null
        currentData.primary = null;
    }
    
    // Update the hidden input
    sdgGoalsInput.value = JSON.stringify(currentData);
    
    // Remove the badge from display
    badge.remove();
    
    // If no badges left, hide the container and reset status
    if (currentData.goals.length === 0) {
        detectedSdgs.classList.add('d-none');
        sdgDetectionStatus.innerHTML = '<small><i class="fas fa-info-circle"></i> SDG goals will be automatically detected from your event description</small>';
    }
}
