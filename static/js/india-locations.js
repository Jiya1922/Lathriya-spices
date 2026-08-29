/**
 * Official Indian States, Union Territories & Districts Data & Searchable Dropdown Utility
 * Source: Official Government of India (LGD / India.gov.in)
 */

const INDIA_LOCATIONS = {
    "Andaman and Nicobar Islands": ["Nicobar", "North and Middle Andaman", "South Andaman"],
    "Andhra Pradesh": ["Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya", "Bapatla", "Chittoor", "East Godavari", "Eluru", "Guntur", "Kakinada", "NTR", "Nandyal", "Palnadu", "Parvathipuram Manyam", "Prakasam", "Sri Potti Sriramulu Nellore", "Sri Sathya Sai", "Srikakulam", "Tirupati", "Visakhapatnam", "Vizianagaram", "West Godavari", "YSR Kadapa"],
    "Arunachal Pradesh": ["Anjaw", "Changlang", "Dibang Valley", "East Kameng", "East Siang", "Itanagar Capital Complex", "Kamle", "Kra Daadi", "Kurung Kumey", "Lepa Rada", "Lohit", "Longding", "Lower Dibang Valley", "Lower Subansiri", "Namsai", "Pakke Kessang", "Papum Pare", "Shi Yomi", "Siang", "Tawang", "Tirap", "Upper Siang", "Upper Subansiri", "West Kameng", "West Siang"],
    "Assam": ["Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hojai", "Jorhat", "Kamrup", "Kamrup Metropolitan", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Morigaon", "Nagaon", "Nalbari", "Sivasagar", "Sonitpur", "South Salmara-Mankachar", "Tinsukia", "Udalguri", "West Karbi Anglong"],
    "Bihar": ["Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur", "Buxar", "Darbhanga", "East Champaran (Motihari)", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur (Bhabua)", "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"],
    "Chandigarh": ["Chandigarh"],
    "Chhattisgarh": ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dantewada (South Bastar)", "Dhamtari", "Durg", "Gariaband", "Gaurela-Pendra-Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham (Kawardha)", "Kanker (North Bastar)", "Khairagarh-Chhuikhadan-Gandai", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Manendragarh-Chirmiri-Bharatpur", "Mohla-Manpur-Ambagarh Chowki", "Mungeli", "Narayanpur", "Raigarh", "Raipur", "Rajnandgaon", "Sakti", "Sarangarh-Bilaigarh", "Sukma", "Surajpur", "Surguja"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
    "Delhi": ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"],
    "Goa": ["North Goa", "South Goa"],
    "Gujarat": ["Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udepur", "Dahod", "Dang", "Devbhumi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad"],
    "Haryana": ["Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"],
    "Himachal Pradesh": ["Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una"],
    "Jammu and Kashmir": ["Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur"],
    "Jharkhand": ["Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum"],
    "Karnataka": ["Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayanagara", "Vijayapura", "Yadgir"],
    "Kerala": ["Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"],
    "Ladakh": ["Kargil", "Leh"],
    "Lakshadweep": ["Lakshadweep"],
    "Madhya Pradesh": ["Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori", "Guna", "Gwalior", "Harda", "Indore", "Jabalpur", "Jhabua", "Katni", "Khandwa", "Khargone", "Maihar", "Mandla", "Mandsaur", "Mauganj", "Morena", "Narsinghpur", "Neemuch", "Niwari", "Narmadapuram", "Pandhurna", "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"],
    "Maharashtra": ["Ahilyanagar (Ahmednagar)", "Akola", "Amravati", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Chhatrapati Sambhaji Nagar", "Dharashiv", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"],
    "Manipur": ["Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul"],
    "Meghalaya": ["East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "Eastern West Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills"],
    "Mizoram": ["Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saitual", "Serchhip", "Siaha"],
    "Nagaland": ["Chumoukedima", "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Niuland", "Noklak", "Peren", "Phek", "Shamator", "Tseminyu", "Tuensang", "Wokha", "Zunheboto"],
    "Odisha": ["Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Sonepur", "Sundargarh"],
    "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"],
    "Punjab": ["Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Firozpur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Malerkotla", "Mansa", "Moga", "Pathankot", "Patiala", "Rupnagar", "Sahibzada Ajit Singh Nagar (Mohali)", "Sangrur", "Shahid Bhagat Singh Nagar", "Sri Muktsar Sahib", "Tarn Taran"],
    "Rajasthan": ["Ajmer", "Alwar", "Anupgarh", "Balotra", "Banswara", "Baran", "Barmer", "Beawar", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Deeg", "Dholpur", "Didwana-Kuchaman", "Dudu", "Dungarpur", "Gangapur City", "Hanumangarh", "Jaipur", "Jaipur Rural", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Jodhpur Rural", "Karauli", "Kekri", "Khairthal-Tijara", "Kota", "Kotputli-Behror", "Nagaur", "Neem Ka Thana", "Pali", "Phalodi", "Pratapgarh", "Rajsamand", "Salumbar", "Sanchore", "Sawai Madhopur", "Shahpura", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur"],
    "Sikkim": ["Gangtok", "Gyalshing", "Mangan", "Namchi", "Pakyong", "Soreng"],
    "Tamil Nadu": ["Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"],
    "Telangana": ["Adilabad", "Bhadradri Kothagudem", "Hanamkonda", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Kumuram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Ranga Reddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri"],
    "Tripura": ["Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura"],
    "Uttar Pradesh": ["Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kheri", "Kushinagar", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Raebareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"],
    "Uttarakhand": ["Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"],
    "West Bengal": ["Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"]
};

/**
 * Creates a searchable dropdown wrapper around a native <select> element.
 * Retains native validation and form submission while providing a instant search box.
 */
function attachSearchableSelect(selectEl, placeholderText = "Select an option") {
    if (!selectEl || selectEl.dataset.searchableInitialized) return;
    selectEl.dataset.searchableInitialized = "true";

    // Create custom wrapper element
    const wrapper = document.createElement("div");
    wrapper.className = "searchable-select-wrapper position-relative";

    const button = document.createElement("button");
    button.type = "button";
    button.className = selectEl.className + " d-flex justify-content-between align-items-center text-start text-truncate bg-white";
    button.style.cursor = "pointer";
    button.style.setProperty("background-image", "none", "important");
    button.style.paddingRight = "0.75rem";

    const labelSpan = document.createElement("span");
    labelSpan.className = "text-truncate me-2";
    labelSpan.textContent = selectEl.options[selectEl.selectedIndex]?.text || placeholderText;

    const arrowIcon = document.createElement("i");
    arrowIcon.className = "fa-solid fa-chevron-down text-muted small ms-1";
    button.appendChild(labelSpan);
    button.appendChild(arrowIcon);

    // Dropdown Container
    const dropdownMenu = document.createElement("div");
    dropdownMenu.className = "searchable-dropdown-menu shadow-sm border rounded bg-white p-2 d-none position-absolute w-100";
    dropdownMenu.style.zIndex = "1050";
    dropdownMenu.style.top = "100%";
    dropdownMenu.style.left = "0";
    dropdownMenu.style.marginTop = "4px";

    // Search Input
    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.className = "form-control form-control-sm mb-2";
    searchInput.placeholder = "Type letters to search...";
    searchInput.autocomplete = "off";

    // Options List Container
    const listContainer = document.createElement("div");
    listContainer.className = "searchable-options-list overflow-auto";
    listContainer.style.maxHeight = "200px";

    dropdownMenu.appendChild(searchInput);
    dropdownMenu.appendChild(listContainer);

    // Insert wrapper into DOM
    selectEl.parentNode.insertBefore(wrapper, selectEl);
    wrapper.appendChild(selectEl);
    wrapper.appendChild(button);
    wrapper.appendChild(dropdownMenu);

    // Hide original select visually, but keep accessible for form submission & HTML5 validation
    selectEl.style.position = "absolute";
    selectEl.style.opacity = "0";
    selectEl.style.height = "0";
    selectEl.style.width = "0";
    selectEl.style.padding = "0";
    selectEl.style.border = "none";
    selectEl.style.pointerEvents = "none";

    function updateOptionsList() {
        listContainer.innerHTML = "";
        const query = searchInput.value.toLowerCase().trim();
        let matchCount = 0;

        Array.from(selectEl.options).forEach((opt) => {
            const text = opt.text;
            const val = opt.value;

            if (query && !text.toLowerCase().includes(query) && val !== "") {
                return;
            }

            matchCount++;
            const item = document.createElement("div");
            item.className = `searchable-option-item px-2 py-1 rounded small ${opt.selected ? "bg-success text-white fw-bold" : "text-dark"}`;
            item.style.cursor = "pointer";
            item.textContent = text;

            item.addEventListener("click", (e) => {
                e.stopPropagation();
                selectEl.value = val;
                selectEl.dispatchEvent(new Event("change", { bubbles: true }));
                closeDropdown();
            });

            item.addEventListener("mouseenter", () => {
                if (!opt.selected) item.classList.add("bg-light");
            });
            item.addEventListener("mouseleave", () => {
                if (!opt.selected) item.classList.remove("bg-light");
            });

            listContainer.appendChild(item);
        });

        if (matchCount === 0) {
            const noRes = document.createElement("div");
            noRes.className = "text-muted small px-2 py-1 italic";
            noRes.textContent = "No matching options found";
            listContainer.appendChild(noRes);
        }
    }

    function syncButtonLabel() {
        const selectedOpt = selectEl.options[selectEl.selectedIndex];
        if (selectedOpt && selectedOpt.value !== "") {
            labelSpan.textContent = selectedOpt.text;
            button.classList.remove("text-muted");
        } else {
            labelSpan.textContent = placeholderText;
            button.classList.add("text-muted");
        }
    }

    function openDropdown() {
        dropdownMenu.classList.remove("d-none");
        searchInput.value = "";
        updateOptionsList();
        setTimeout(() => searchInput.focus(), 50);
    }

    function closeDropdown() {
        dropdownMenu.classList.add("d-none");
    }

    button.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (dropdownMenu.classList.contains("d-none")) {
            // Close any other open searchable dropdowns
            document.querySelectorAll(".searchable-dropdown-menu").forEach((m) => m.classList.add("d-none"));
            openDropdown();
        } else {
            closeDropdown();
        }
    });

    searchInput.addEventListener("input", updateOptionsList);

    searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeDropdown();
            button.focus();
        }
    });

    document.addEventListener("click", (e) => {
        if (!wrapper.contains(e.target)) {
            closeDropdown();
        }
    });

    selectEl.addEventListener("change", () => {
        syncButtonLabel();
        updateOptionsList();
    });

    // Custom method to refresh options when select content is modified dynamically
    selectEl.refreshSearchable = function () {
        syncButtonLabel();
        updateOptionsList();
    };

    syncButtonLabel();
}

/**
 * Initializes cascading State & District dropdowns across India
 */
function initLocationSelector(stateSelectId, districtSelectId, initialSelectedState = "", initialSelectedDistrict = "") {
    const stateEl = document.getElementById(stateSelectId);
    const districtEl = document.getElementById(districtSelectId);

    if (!stateEl || !districtEl) return;

    // 1. Populate State Dropdown
    stateEl.innerHTML = '<option value="">Select State / UT</option>';
    const sortedStates = Object.keys(INDIA_LOCATIONS).sort();

    sortedStates.forEach((stateName) => {
        const opt = document.createElement("option");
        opt.value = stateName;
        opt.textContent = stateName;
        if (initialSelectedState && stateName.toLowerCase() === initialSelectedState.toLowerCase()) {
            opt.selected = true;
        }
        stateEl.appendChild(opt);
    });

    // 2. Populate District Dropdown based on State
    function updateDistrictOptions(selectedState, selectedDistrict = "") {
        districtEl.innerHTML = "";

        if (!selectedState || !INDIA_LOCATIONS[selectedState]) {
            districtEl.innerHTML = '<option value="">Select State First</option>';
            districtEl.disabled = true;
        } else {
            districtEl.disabled = false;
            const defaultOpt = document.createElement("option");
            defaultOpt.value = "";
            defaultOpt.textContent = "Select District";
            districtEl.appendChild(defaultOpt);

            const districts = INDIA_LOCATIONS[selectedState].slice().sort();
            districts.forEach((distName) => {
                const opt = document.createElement("option");
                opt.value = distName;
                opt.textContent = distName;
                if (selectedDistrict && distName.toLowerCase() === selectedDistrict.toLowerCase()) {
                    opt.selected = true;
                }
                districtEl.appendChild(opt);
            });
        }

        if (typeof districtEl.refreshSearchable === "function") {
            districtEl.refreshSearchable();
        }
    }

    // 3. Initial Populate
    const currentSelectedState = stateEl.value || initialSelectedState;
    updateDistrictOptions(currentSelectedState, initialSelectedDistrict);

    // 4. Attach Searchable Select Enhancements
    attachSearchableSelect(stateEl, "Select State / UT");
    attachSearchableSelect(districtEl, "Select District");

    // 5. Change Listener for State
    stateEl.addEventListener("change", function () {
        const newState = this.value;
        updateDistrictOptions(newState, "");
    });
}
