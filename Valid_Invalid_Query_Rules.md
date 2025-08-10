Based on the classifier implementation and the goal of creating a Perplexity-like AI assistant, here are the clear requirements for query validity:

## ✅ **VALID Queries (Information Requests)**

### **1. Factual Questions**
- "What is machine learning?"
- "How does photosynthesis work?"
- "When was the internet invented?"
- "Where is the Great Wall of China?"

### **2. How-To & Tutorial Requests**
- "How to cook pasta?"
- "How to learn Python programming?"
- "Steps to start a business"
- "Guide to meditation"

### **3. Explanations & Definitions**
- "Explain quantum computing"
- "Define artificial intelligence"
- "What does blockchain mean?"
- "Tell me about climate change"

### **4. Comparisons & Analysis**
- "Compare Python vs JavaScript"
- "iPhone vs Android differences"
- "Pros and cons of electric cars"
- "Which is better: React or Vue?"

### **5. Research & Statistics**
- "Latest AI developments"
- "Statistics on climate change"
- "Research on COVID-19 vaccines"
- "Data on renewable energy adoption"

### **6. Recommendations & Reviews**
- "Best laptops for programming"
- "Top restaurants in New York"
- "Recommended books on AI"
- "Best practices for remote work"

### **7. News & Current Events**
- "Latest news about AI"
- "Recent developments in space exploration"
- "Current economic trends"
- "Breaking news about technology"

## ❌ **INVALID Queries (Action Commands & Non-Information Requests)**

### **1. Device/App Control Commands**
- "Set alarm for 6am"
- "Turn off the lights"
- "Play music"
- "Open calculator"
- "Take a photo"

### **2. Communication Commands**
- "Call mom"
- "Send email to John"
- "Text my friend"
- "Message the team"

### **3. Booking & Purchase Commands**
- "Book a flight to Paris"
- "Buy groceries"
- "Order pizza"
- "Reserve a table"

### **4. Personal Reminders & Calendar**
- "Remind me to buy milk"
- "Schedule meeting for tomorrow"
- "Set appointment with doctor"
- "Add event to calendar"

### **5. Random Text & Gibberish**
- "hello"
- "ok"
- "test test test"
- "walk my apples for my dog"
- "efofjseofijesfo?"

### **6. Single Words Without Context**
- "yes"
- "no"
- "a"
- "test"
- "blah"

### **7. Commands to Control Systems**
- "Delete my account"
- "Change password"
- "Update my profile"
- "Install software"

## 🎯 **Key Decision Criteria**

### **VALID if:**
- ✅ Seeks **information** or **knowledge**
- ✅ Asks a **question** or requests **explanation**
- ✅ Requests **guidance** or **instructions**
- ✅ Asks for **comparison** or **analysis**
- ✅ Seeks **statistics** or **data**
- ✅ Requests **recommendations** or **reviews**
- ✅ Asks about **current events** or **news**

### **INVALID if:**
- ❌ Commands to **perform an action**
- ❌ Requests to **control devices** or **apps**
- ❌ Asks to **book**, **buy**, or **purchase** something
- ❌ Requests **personal reminders** or **calendar management**
- ❌ **Random text** or **gibberish**
- ❌ **Single words** without meaningful context
- ❌ Commands to **modify system settings**

## 📝 **Examples for Testing**

### **Should be VALID:**
- "What is the weather today?" (information request)
- "How to make bread?" (how-to request)
- "Compare electric vs gas cars" (comparison)
- "Latest news about space exploration" (news request)
- "Best programming languages for beginners" (recommendation)

### **Should be INVALID:**
- "Set alarm for 6am" (action command)
- "Call my mom" (communication command)
- "Book a hotel in Paris" (booking command)
- "hello" (random text)
- "walk my apples for my dog" (nonsensical)
- "Turn off the lights" (device control)

This classification ensures that only information-seeking queries are processed by the web search and content analysis pipeline, while action commands and nonsensical queries are rejected early.