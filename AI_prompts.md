# AI Prompts — Homework 4: Campus Customs E-Commerce Site with AI Shopping Assistant

This file records the prompts the student submitted to the AI coding assistant (Claude Code), problem by problem.
It is updated as the work happens, not reconstructed at the end.

Recording rules:

- Prompts are copied verbatim from what the student submitted. They are not paraphrased, polished, or invented.
- Each problem has an initial prompt, any follow-up prompts, and (when applicable) a short note on what was
  missing or needed improvement after the initial attempt.
- If a single message was submitted in several pasted parts, all parts are recorded together in their original order.

---

## Problem 1 — Project Setup, Documentation System, and Environment Readiness

### Initial prompt

```text
I'm starting Homework 4 for my AI Foundations course. The project involves building a Campus Customs e-commerce website with an AI shopping assistant.
Before we begin implementing the individual problems, I want you to establish the project organization and documentation system.
1. Create the project structure
Create a root folder named `hw4` with the following organization:

* `AI_prompts.md`
* `README.md`
* `requirements.txt`
* `.gitignore`
* `.env.example`
* `frontend/`
* `backend/`
   * `main.py`
   * `agent.py`
   * `models.py`
   * `tools.py`
   * `prompts/prompt.md`
* `output/`
   * `harness.md`
   * `design.md`
   * `usability.md`
   * `app_check.html`
   * `app_check_images/`
   * `audit_trail.json`
* `data/` (local files only, excluded from GitHub)

Create the necessary directories and placeholder files, but do not implement application features yet.
2. Establish the AI prompt documentation process
The file `AI_prompts.md` is a required deliverable and must be maintained throughout the assignment.
For every problem, create a separate section containing:

* The problem number and title.
* The initial prompt I actually submitted to you.
* Any follow-up prompts I submitted to refine or correct the implementation.
* A brief explanation of what was missing or needed improvement after the initial attempt, when applicable.

Record my prompts accurately and preserve my original wording as much as possible. Do not invent prompts, rewrite them to sound more sophisticated, or create fictional interactions.
Update this document continuously as we work, rather than reconstructing it at the end.
This initial setup request should be recorded under Problem 1.
3. Establish standing workflow instructions
For the remainder of this assignment:

* Work on one problem at a time, only when I explicitly direct you to proceed.
* Do not anticipate or implement future problems unless I request them.
* Maintain the existing project structure and build upon completed work.
* Update the appropriate documentation files as features are implemented.
* Explain any major implementation decisions or technical issues in plain English.
* Test functionality when possible and report what was actually verified.
* If something cannot be tested, clearly identify it rather than assuming it works.
* Do not overwrite existing files, assets, or working code without checking their contents first.

4. Protect sensitive information
The project will eventually be published to a public GitHub repository.
Configure `.gitignore` to exclude:

* `.env` files containing real credentials
* The SQLite database
* Product image assets
* Python virtual environments and cache files
* Node dependencies and generated build files
* Other local secrets or unnecessary generated files

Create `.env.example` using placeholder values only. Do not copy real API keys into it.
The database and product images must remain available locally for development but must never be committed to GitHub.
5. Prepare for future development
The application will eventually use React, Vite, and TypeScript for the frontend, and FastAPI with PydanticAI for the backend.
For now, only establish the organization and documentation framework. Do not install dependencies, build the application, or connect to APIs yet.
When finished, show me the project directory structure, confirm that `AI_prompts.md` has been initialized, and identify anything that still needs to be provided before we start Problem 2.

6. Check and prepare the development environment
Before we start building the website, please perform a development environment readiness check.
Verify that we have the tools and dependencies needed for this assignment, including:

* Python and pip
* Node.js and npm
* Git and GitHub connectivity
* React, Vite, and TypeScript project tooling
* FastAPI and Uvicorn
* Pydantic and PydanticAI
* SQLite support
* HTTP client dependencies needed for frontend/backend communication
* Any additional packages necessary to connect the PydanticAI agent to an AI model through Portkey or another configured provider

For each tool or dependency:

1. Check whether it is already installed and whether its version is compatible with the project.
2. If it is missing, install an appropriate stable compatible version using the official package manager or installation method.
3. Prefer project-local dependencies and a Python virtual environment rather than unnecessary system-wide installations.
4. Avoid reinstalling tools that are already working.
5. Verify successful installation using appropriate version checks, imports, or basic commands.
6. Record the project dependencies in `requirements.txt` and the frontend package configuration as appropriate.

Please also check whether my development environment can access the AI provider configuration needed for the chatbot. Do not display, copy into documentation, or expose any actual API keys or other secrets.
If installation requires administrator privileges, changing security settings, or making major changes to my computer, ask for permission first.
Check that the project's Git configuration is ready for eventual GitHub submission, but do not create or publish the repository yet.
Do not start building the website or implementing Problems 2–13.
When you're finished, give me a short readiness report showing:

* Tools already available
* Tools or dependencies you installed
* Results of the installation checks
* Any remaining issues that could prevent us from completing the assignment
* Whether we're ready to begin Problem 2
```

### Follow-up prompts

#### Follow-up 1

```text
Before moving to Problem 2, please create or update a project-level `CLAUDE.md` containing the standing workflow instructions from Problem 1, including maintaining AI_prompts.md, working one problem at a time, accurately documenting follow-up prompts, protecting sensitive files, and testing completed features.

Check for existing instructions before making changes, and avoid duplicating them. Record this follow-up prompt in AI_prompts.md.

Do not implement Problem 2 yet.
```

#### Follow-up 2

```text
@"C:\Users\kcduf\Downloads\data (3).zip"
```

_(Supplied the course data archive: the SQLite database and the product images, unpacked into `data/`.)_

### What was missing or needed improvement

After the initial setup, the standing workflow instructions were only stated in the conversation and saved in the
assistant's private memory, not in a project file. Follow-up 1 asked for a project-level `hw4/CLAUDE.md`
so those rules stay with the project.

---

## Problem 2 — Database Detective

### Initial prompt

```text
Let's begin Problem 2: Database Detective.
The Campus Customs SQLite database and product images are now available in `hw4/data/`.
Please inspect the database thoroughly and create the database documentation required for Problem 2.
For each table, document:

* Table name and purpose
* Column names and SQLite data types
* Primary and foreign keys
* Relationships between tables
* Important constraints
* Any relevant observations about the data that may affect development

Also identify how product information, inventory quantities, user accounts, and saved chat messages relate to one another.
Save the findings in the appropriate project documentation file, using clear, organized Markdown tables where helpful.
Do not modify the database or implement application features yet.
Explain your findings in plain English, including anything we should be aware of before building the website.
As always, record this prompt accurately under Problem 2 in `AI_prompts.md` and maintain our established documentation workflow.
When finished, show me the documentation location and summarize the findings so I can review them before we proceed to Problem 3.
```

### Follow-up prompts

_No follow-up prompts recorded yet._

### What was missing or needed improvement

_Nothing recorded yet._
---

## Problem 3 — Building the Campus Customs Website

### Initial prompt

```text
Let's begin Problem 3: Building the Campus Customs Website.
I want to build a functional, user-friendly e-commerce website for Campus Customs, a Yale-themed clothing store. Please use our existing project structure and the SQLite database and product images we've already prepared.
The website should feel like a legitimate online clothing retailer, not a generic coding demonstration.
1. Frontend development
Use React, Vite, and TypeScript to create the frontend.
Build the following pages and components:

* A homepage with Campus Customs branding and an introduction to the store.
* A product catalogue displaying the available merchandise from the SQLite database.
* Individual product detail pages that shoppers can open by selecting an item.
* A navigation menu that makes it easy to move between the homepage and catalogue.
* A chat interface that will eventually connect to our AI shopping assistant.

The website should have a responsive layout that works on desktop and mobile screens.
2. Product catalogue
Connect the website to the existing `campus_customs.db` SQLite database through the FastAPI backend.
Retrieve actual product information from the `catalogue` table, including product names, descriptions, garment types, colors, prices, and image references.
Use the corresponding product images from `hw4/data/products/`.
Display products as visually organized cards with their images, names, and prices.
Each product card should open a dedicated detail page containing the product's complete information and available sizes.
Display real inventory quantities or availability from the `inventory` table. Do not invent products, prices, or stock information.
Remember that the database has inconsistent garment-type labels and colors. Handle these variations appropriately without modifying the original database.
3. Backend integration
Use FastAPI to create the API endpoints necessary for the storefront.
The frontend should retrieve catalogue and inventory information through the API rather than accessing SQLite directly.
Serve product images from the local data directory through the backend.
Keep database access organized so that later problems can add user authentication, AI tools, product searches, and chat history without requiring major restructuring.
4. Chat interface
Create a floating chat widget that shoppers can open and close while browsing the website.
The widget should include:

* A conversation display area.
* A message input field.
* A send button.
* A welcoming introduction for the Campus Customs shopping assistant.
* A clear visual distinction between shopper messages and assistant messages.

For now, the chat interface only needs to be visually and structurally ready.
Do not implement the AI agent, connect to Portkey, or create simulated chatbot responses yet. Those features belong to later problems.
5. Initial visual design
Use a clean Yale-inspired aesthetic, with Yale blue, white, and complementary neutral colors.
I want the website to look polished, professional, and easy to navigate.
Use sensible typography, appropriate spacing, and a consistent layout.
We already have custom Handsome Dan design assets prepared for this assignment. We will incorporate those during the visual design phase, so please build the frontend in a way that makes adding custom illustrations, animations, and branding straightforward later.
Do not spend excessive time creating new illustrations or animations at this stage.
6. Technical requirements

* Use the existing project-local dependencies where possible.
* Keep frontend and backend code organized in their respective directories.
* Use parameterized SQLite queries.
* Validate API inputs and handle missing products gracefully.
* Configure frontend/backend communication correctly for local development.
* Preserve the existing database without changing its schema or contents.
* Keep API credentials and other secrets outside source code.
* Avoid implementing authentication, customer memory, or AI agent functionality, as these belong to later problems.

7. Documentation
Continue following our established documentation workflow.

* Record this prompt accurately under Problem 3 in `AI_prompts.md`.
* Record any subsequent troubleshooting or revision prompts.
* Update `output/design.md` with the application architecture and frontend/backend organization, preserving the database documentation from Problem 2.
* Document any decisions that will affect later development.

8. Testing and completion
After implementation:

1. Start the backend and frontend development servers.
2. Verify that the website loads successfully.
3. Confirm that all 102 products are retrieved from the database.
4. Test navigation between the homepage, catalogue, and individual product pages.
5. Check that prices, images, and stock availability match the database.
6. Verify that the chat widget opens and closes and accepts input without generating fake AI responses.
7. Check for obvious errors in the browser or server logs.
8. Run the TypeScript build and any relevant backend checks.

If browser-based testing is unavailable, tell me what you verified programmatically and what I'll need to check manually.
Please fix any errors discovered during testing before declaring Problem 3 complete.
When finished, give me a concise summary of what was built, what was tested, the commands or URLs needed to view the website, and anything that remains unfinished.
Do not proceed to Problem 4 until I approve the result.
```

### Follow-up prompts

_No follow-up prompts recorded yet._

### What was missing or needed improvement

_Nothing recorded yet._
---

## Problem 4 — Customer Accounts: Registration, Login, and Logout

### Initial prompt

```text
Okay, Problem 3 looks good. I've tested the website myself, and the products and chat interface are working as expected. Let's move on to Problem 4.

Now we need customers to be able to create accounts, log in, and log out.

I want the registration and login process to feel like a normal shopping website. Customers should be able to enter their information, create an account, and then log back in without losing their account information.

Please follow the specific password security and authentication requirements from Problem 4, including the required hashing method. We already found that the database contains three existing users, so make sure we investigate how those passwords were originally hashed before deciding whether those accounts can be authenticated.

The professor also provided a test account in the instructions. Please use that information to verify the login functionality, but don't include any actual passwords in our public documentation or source code.

Make sure the system handles things like incorrect passwords, duplicate accounts, and missing information appropriately. I don't want customers seeing technical error messages or having the site crash when they make a mistake.

Keep the account interface consistent with the website we've already built, and make sure everything works on mobile as well.

Don't change the original database structure unless it's genuinely necessary, and explain any changes before making them. Don't reset or replace the existing users.

As usual, document this prompt in AI_prompts.md, update the relevant technical documentation, and thoroughly test the registration, login, and logout functionality.

Please tell me what you tested, whether the professor's test account worked, and whether anything still needs attention.

Don't move on to Problem 5 yet. I want to test the login process myself first.
```

### Follow-up prompts

#### Follow-up 1

_The test account's email and password are replaced with `[REDACTED: …]` placeholders because this file will be public. Everything else is verbatim._

```text
Okay, I have the specific requirements from the professor for Problem 4.
We need a normal account creation and login system. Registration should collect first name, last name, email, and password. I'd also like a confirm-password field to help prevent mistakes. Login should use email and password, and new accounts should be saved in the existing users table.
The professor provided the following test account:
Email: [REDACTED: provided test account email]
Password: [REDACTED: provided test account password]
Here are the exact password security requirements:

* Use PBKDF2-HMAC-SHA256 with 120,000 iterations.
* Store password hashes in the format `pbkdf2_sha256$salt$hash`.
* When someone logs in, extract the existing salt from their stored hash rather than generating a new one.
* Hash the password they entered using the same salt and settings, then compare it with the stored hash using a constant-time comparison.
* Registration and login must use matching hashing settings.

Please use these specifications to finish investigating the existing accounts and implement Problem 4.
I want customers to be able to register, log in, and log out normally, with clear messages if they enter incorrect information or try to create an account with an email that's already registered.
Please also make sure:

* The seeded test account can successfully log in.
* A brand-new account can be created and then used to log in.
* Passwords are never stored in plain text.
* Existing accounts and data are preserved.
* The registration and login pages match the storefront we've already built.
* The login experience works on mobile as well as desktop.

Update `output/harness.md` to explain how authentication works, what information is stored for each user, and how passwords are protected.
Continue documenting our actual prompts in `AI_prompts.md`. Don't include passwords or other credentials in the public documentation. You can identify the professor's account as the provided test account without recording its password.
Test everything before reporting back. Please let me know specifically whether both the seeded account and a newly created account successfully logged in.
Don't proceed to Problem 5 yet. I want to review and test this first.
```

#### Follow-up 2

```text
Before we move on to Problem 5, can you do one final round of testing on Problem 4 for me?
I want you to test the website the way an actual customer would, using the browser rather than just checking the backend code.
Please:

1. Log in using the professor's provided test account and confirm it works.
2. Create a brand-new customer account, then log out and log back in with that account.
3. Refresh the page and navigate between products to confirm the customer stays signed in.
4. Try an incorrect password and confirm the error message is clear.
5. Check that the login and registration pages work on both desktop and mobile.
6. Confirm that logging out actually ends the browser's authenticated session.

Use the existing test credentials securely, and use a temporary copy of the database for any new test accounts so we don't unnecessarily alter the original data.
Please fix any issues you discover, document any corrections, and record this prompt in AI_prompts.md.
When finished, give me a short pass/fail report. If everything works, we can consider Problem 4 complete. Don't start Problem 5 yet.
```

### What was missing or needed improvement

The initial prompt referred to the professor's Problem 4 requirements and test account, but neither was in the
conversation or the project files. The assistant did not guess the hashing settings. It asked for them, and no code
was written. Follow-up 1 supplied the required hashing method (PBKDF2-HMAC-SHA256, 120,000 iterations,
`pbkdf2_sha256$salt$hash`, stored salt re-used at login, constant-time comparison), the registration fields
(including confirm password), and the test account. With those, the existing hashes were confirmed to match the
specification, with the salt used as UTF-8 text, and the feature was built.

Follow-up 2 asked for a final round of customer-style browser testing. All six checks passed, but it uncovered one
problem: on a small phone (360×640), submitting the registration form with mistakes left the error messages above
the visible area, so nothing seemed to happen. The forms now move focus to the first problem field, or to the error
message, after a failed submit. The details are in `output/harness.md`, section 1.9.
---

## Problem 5 — AI Shopping Assistant (PydanticAI + FastAPI Chat)

### Initial prompt

```text
Okay, Problem 4 is complete and all of the testing passed! Let's move on to Problem 5 and get the AI shopping assistant working.
We already have the Campus Customs website, the chat interface, and our Portkey connection set up. Now I want customers to actually be able to have a conversation with the assistant.
The professor specifically wants us to use PydanticAI with FastAPI, so let's build on what we already have rather than starting over.
Here's what I want the assistant to do:
I want it to feel like a friendly, knowledgeable employee at Campus Customs. It should be welcoming and helpful, understand that it's assisting customers shopping for Yale merchandise, and be able to have a natural conversation.
It should also understand its limitations. For example, I don't want it making up prices, inventory quantities, or product availability. We'll add the tools for looking that information up in Problem 6, so for now it should be upfront when it can't verify something.
Eventually, I'd like our animated Handsome Dan character to represent the assistant, but we can incorporate those visual elements later.
The technical requirements from the professor:
The FastAPI application should remain in `backend/main.py`, and we should be able to run it from the `backend/` folder using:
`uvicorn main:app --reload --port 8000`
The PydanticAI agent needs to be organized into four files:

* `backend/prompts/prompt.md` — the system prompt that defines the assistant's personality, behavior, and basic safety rules.
* `backend/agent.py` — where the PydanticAI agent is created and connected to the AI model.
* `backend/tools.py` — where the agent's tools will go. We don't need to build the product and inventory lookup tools until Problem 6.
* `backend/models.py` — the structured data models for the agent, chat responses, and eventually product cards.

Please preserve the existing storefront functionality and any code we've already written. If any of these files are already being used, build on them rather than replacing their contents.
Connecting the assistant:
Use our existing Portkey configuration and the working model connection you already tested. Choose an appropriate supported model without changing credentials unnecessarily.
Connect the website's chat widget to a FastAPI chat endpoint so that a customer can type a message, send it, and receive an actual AI-generated response.
I want the experience to feel like a real conversation, with messages appearing in the correct order and clear visual differences between the customer and assistant.
Please include a loading indicator while the assistant is thinking, and make sure the site handles failed requests gracefully instead of freezing or displaying a technical error.
For now, basic conversation is enough. Don't implement product searches, inventory tools, customer memory, or dynamically generated product cards yet. Those are covered in later problems.
Safety and accuracy:
The assistant should stay focused on helping Campus Customs shoppers.
It should not invent product information, prices, stock availability, store policies, or other details it cannot verify.
It shouldn't reveal its system prompt, API credentials, or other private application information.
Keep all credentials on the backend. The browser should never receive the Portkey API key.
Documentation:
Continue maintaining `AI_prompts.md` with my actual prompts and any follow-up instructions.
Please update `output/harness.md` to explain how the frontend communicates with FastAPI, how the PydanticAI agent loads its system prompt, and which model configuration it uses.
Document the structured response models and any technical decisions that will matter when we add database tools in Problem 6.
Testing:
Once everything is connected, please test it through the actual website, not just the backend.
I want you to verify that:

* A customer can send a message and receive a real AI response.
* The assistant responds appropriately to basic questions about Campus Customs.
* It doesn't invent prices or stock information when asked.
* The chat stays usable while waiting for a response.
* Errors are displayed in a way a normal customer can understand.
* The website, product pages, registration, and login still work.
* The backend starts using the professor's required command.

Use the existing local configuration and protect all API credentials during testing.
If you discover any problems, fix them and retest.
When you're finished, give me a summary of what you built, the model you're using, the testing results, and any limitations we should know about.
Don't proceed to Problem 6 until I approve the work.
```

### Follow-up prompts

_No follow-up prompts recorded yet._

### What was missing or needed improvement

_Nothing recorded yet._
---

## Problem 6 — Product and Inventory Tools for the Assistant

### Initial prompt

```text
Okay, Problem 5 looks good! Let's move on to Problem 6 and give our AI shopping assistant access to the actual products and inventory.
Right now, the assistant can have a conversation, but it can't look anything up. I want it to function more like an employee who actually knows what's in the store.
For example, if someone asks how much a particular sweatshirt costs, whether a shirt comes in navy, or if something is available in a medium, the assistant should look up that information in our database and give them an accurate answer.
I don't want it guessing or making up information, especially when it comes to prices or availability.
Here's what we need to build:
The professor wants the agent to have two separate database tools: one for retrieving product information and another for checking inventory.
Please implement these using PydanticAI's tool functionality in `backend/tools.py` and connect them to our existing agent.
The product information tool should be able to retrieve relevant details from the `catalogue` table, including product names, descriptions, garment types, colors, prices, and anything else useful for answering customer questions.
The inventory tool should check the `inventory` table and return accurate stock information for specific products and sizes.
Both tools should use our existing database connection and catalogue code where possible. I don't want us duplicating functionality or changing the original database unnecessarily.
How I want the assistant to behave:

* When a customer asks about a specific product, the assistant should use the database to verify its response.
* When someone asks about size availability, it should check the actual inventory instead of assuming something is in stock.
* If a size is sold out, it should say so clearly.
* If a product doesn't exist or the request is ambiguous, it should explain that or ask a clarifying question.
* It should be able to understand natural shopping questions, even when customers don't use the exact product names from the database.
* It should handle the inconsistent product category and color descriptions we identified in Problem 2.
* It should never invent product names, prices, colors, or inventory quantities.
* It shouldn't promise that stock is reserved or that checkout is available.

For now, the assistant can explain its findings in the chat. We'll create clickable product recommendation cards in Problem 7, so don't implement those yet.
Technical requirements:
Use PydanticAI's supported tool registration methods for the version we already installed.
Keep the tools in `backend/tools.py`, with the agent itself in `backend/agent.py`.
Make sure the product and inventory tools query the actual SQLite database and return useful structured information to the agent.
Use safe, parameterized database queries and handle missing or invalid product IDs and sizes gracefully.
Keep the existing FastAPI endpoint and frontend chat connection working.
Update `backend/prompts/prompt.md` so the assistant knows when to use each tool and understands that verified database information takes priority over assumptions.
Also, please check the current system prompt for any unsupported claims about the store, including whether Campus Customs is officially affiliated with Yale. Unless the assignment or project data establishes that information, the assistant shouldn't make definitive claims about it.
Testing:
Please test this through the actual website, not just by calling the backend.
I want you to try several types of questions, including:

1. Asking for the price of a product that exists.
2. Asking whether a specific product is available in a particular size.
3. Asking about a size that's sold out.
4. Asking for a product that doesn't exist.
5. Asking a general question like "What kinds of sweatshirts do you have?"
6. Asking about colors or using slightly different wording than the database.
7. Asking the same inventory question in different ways to see if the assistant responds consistently.

Please verify the assistant's answers against the actual database, not just whether they sound reasonable.
Also confirm that the website, login system, and existing chat functionality still work.
If you find inaccuracies, fix them and retest.
Documentation:
Continue recording my actual prompts and follow-up requests in `AI_prompts.md`.
Update `output/harness.md` to explain both tools, what information they retrieve, how they interact with PydanticAI, and how we verified the results.
Update other documentation as needed without overwriting previous sections.
When you're finished, tell me which tools you created, what questions you tested, whether the answers matched the database, and any limitations we should address later.
Don't start Problem 7 until I approve the results.
```

### Follow-up prompts

_No follow-up prompts recorded yet._

### What was missing or needed improvement

_Nothing recorded yet._
---

## Problem 7 — Product Cards in the Shopping Assistant

### Initial prompt

```text
Okay, Problem 6 is looking good! Let's move on to Problem 7 and make the shopping assistant more interactive.
Right now, the assistant can search the database and give customers accurate product information, but it's still mostly communicating through text. I want it to actually show customers the products it's talking about.
For example, if someone asks, "Can you show me some Yale hoodies?" I want the assistant to display the matching products directly in the chat, with pictures, names, and prices. Customers should be able to click on one of those products and go straight to its page on the website.
I want this to feel like a natural part of shopping, not like the assistant is just dumping database results into the conversation.
Here's what we need to accomplish:
The professor wants us to implement dynamic product search and have the chatbot return product cards based on what customers ask for.
Please build on the database tools we created in Problem 6 and the existing React chat interface.
When the assistant searches for merchandise, it should be able to return structured product information alongside its conversational response. The frontend should use that information to display actual product cards.
Each card should include the product image, name, and price, and clicking it should open the corresponding product detail page.
Everything should come from the real database. I don't want the AI generating product names, inventing images, or making up prices.
How I want the shopping experience to work:

* If someone asks to see hoodies, sweatshirts, T-shirts, or other merchandise, show relevant product cards in the chat.
* If they ask for something more specific, like a navy hoodie or a quarter zip, narrow the results accordingly.
* If they mention a size, make sure the recommendations reflect actual inventory for that size.
* Don't recommend a sold-out size as though it's available.
* If multiple products match, show a manageable selection rather than overwhelming the customer with dozens of cards.
* If nothing matches, explain that naturally instead of showing empty or unrelated products.
* If the customer clicks a product, take them to that product's detail page without breaking the chat experience.

I also want the assistant to be able to explain why it's recommending something when appropriate, but those explanations should be grounded in the actual product information.
Technical requirements:
Please use the structured response models in `backend/models.py` and update them as needed so the agent can return both a conversational message and product information.
Connect this to our existing PydanticAI agent and FastAPI chat endpoint.
Use the database tools we already created rather than introducing a separate, inconsistent search system.
The backend should verify that every product returned to the frontend actually exists in the database. Product IDs, images, prices, and inventory information should come from verified records, not AI-generated values.
Have the React chat widget render the product cards from this structured information.
Please also make sure the product images are displayed correctly and that the cards work on mobile screens.
Keep the existing product catalogue, login functionality, and normal chatbot conversations working.
We don't need shopping-cart or checkout functionality, and we shouldn't imply those features are available.
Testing:
Please test this through the actual website, including:

1. A general request to see Yale sweatshirts.
2. A more specific request for navy hoodies.
3. A request for merchandise in a particular size.
4. A request where the requested size is sold out.
5. A product that doesn't exist.
6. Clicking a recommended product card and navigating to its detail page.
7. Asking follow-up questions about a product the assistant just recommended.
8. Checking the product cards on desktop and mobile.

Please compare the products, prices, images, and inventory with the database to make sure everything is accurate.
Also verify that ordinary conversations still work when no product cards are needed.
If you find any problems, fix them and retest.
Documentation:
Continue adding my actual prompts and follow-up instructions to `AI_prompts.md`.
Update `output/harness.md` to explain how product search results become structured chat responses and how the frontend renders the cards.
Update the design documentation as needed, without overwriting anything from the previous problems.
When you're finished, tell me what you built, what you tested, and whether the assistant is reliably displaying the correct products.
Don't move on to Problem 8 yet. I want to review the results first.
```

### Follow-up prompts

_No follow-up prompts recorded yet._

### What was missing or needed improvement

_Nothing recorded yet._
---

## Problem 8 — Customer Memory and Page Context

### Initial prompt

```text
Okay, Problem 7 is complete, and the product cards are working! Let's move on to Problem 8 and give our shopping assistant some customer memory.
Right now, the assistant can remember what we're talking about while the chat is open, but if someone closes the browser or comes back another day, that conversation disappears.
I want returning customers to be able to pick up where they left off instead of starting from scratch every time.
We already have customer accounts, so I'd like the assistant to recognize when someone is signed in, remember their previous conversations, and use that information to make the shopping experience more personal.
For example, if I was looking at navy sweatshirts yesterday, I'd like to be able to log back in and ask, "Can we go back to those sweatshirts we were looking at?" without having to explain everything again.
Here's what I'd like us to build:
Use the existing `chat_messages` table to save conversations for signed-in customers.
Each message should be associated with the correct customer account so conversations can be retrieved when that customer returns.
When someone logs back in, the chat should be able to restore their previous messages, including product recommendations and product cards.
I also want the assistant to understand what product page the customer is currently viewing.
For example, if someone opens a sweatshirt's product page and asks, "Does this come in a large?" the assistant should understand that "this" refers to the sweatshirt they're looking at.
The same applies if they navigate to another product page. The assistant should use the current page context rather than assuming they're still talking about the previous product.
A few things that are important to me:

* Customers should only ever be able to access their own saved conversations.
* Signed-out visitors should still be able to chat, but their conversations shouldn't accidentally become associated with someone else's account.
* If someone logs out and another customer logs in using the same browser, the previous customer's messages shouldn't appear.
* The assistant shouldn't invent memories or claim to remember something that isn't in the saved conversation.
* If a previous product is no longer available, it should check the current database before recommending it again.
* Previous product cards can be restored as part of the conversation, but current product availability should always come from a fresh database lookup.
* The existing New Chat button should continue working. Starting a new conversation shouldn't accidentally erase a customer's saved history.

I'd like the chat to feel natural and convenient, without requiring customers to manage a complicated conversation history system.
Technical requirements:
Please build on our existing React frontend, FastAPI backend, PydanticAI agent, and customer authentication.
Use the existing `chat_messages` table rather than creating a separate database unless there's a genuine reason to do so.
Associate saved messages with the authenticated user on the backend, not with a user ID supplied by the browser.
Make sure the chat endpoint receives the current page context so the assistant knows whether the customer is browsing the homepage, catalogue, or a particular product.
Use the actual product ID from the page when available, and verify that product against the database before the assistant refers to it.
Please be careful with conversation history. I don't want us sending unlimited past messages to the AI model or slowing the chat down unnecessarily. Use a reasonable context window while keeping the full saved history available to the customer.
Also, make sure that restored product cards still work and that the backend doesn't blindly trust product information supplied by the browser.
Keep the current website, product search, inventory tools, login system, and clickable recommendations working.
If the existing database structure has limitations that affect how we can save or organize conversations, explain them and choose the simplest approach that meets the assignment requirements without unnecessarily altering the database.
Testing:
Please test this through the actual website, including:

1. Sign in, have a conversation about products, close or reload the browser, and confirm the conversation comes back.
2. Log out and back in, then confirm the previous conversation is still available.
3. Sign in as a different customer and verify that the first customer's conversations are not visible.
4. Try chatting while signed out and confirm the messages aren't saved under another account.
5. Open a specific product page and ask a question like "Is this available in medium?" without naming the product.
6. Navigate to another product and ask the same question to confirm the assistant understands the new page.
7. Restore a conversation containing product cards and verify that the links still work.
8. Start a new chat, then verify that previous saved messages haven't been unintentionally deleted.
9. Check that saved conversations, account switching, and page context work on mobile as well as desktop.

Please also test that someone cannot retrieve another customer's messages simply by changing request information or manipulating a URL.
Use temporary database copies for tests that create customer accounts or chat history whenever practical. Keep the original database and its seeded records intact.
If you find problems, fix them and retest.
Documentation:
As usual, record my actual prompt and any follow-up instructions in `AI_prompts.md`.
Update `output/harness.md` to explain how chat messages are saved and restored, how customer identity is established, how page context reaches the agent, and how access to conversations is protected.
Update `output/design.md` with any relevant architecture changes without overwriting previous documentation.
When you're finished, give me a summary of what you built, what you tested, how conversation history works, and whether there are any limitations we should know about.
Don't move on to Problem 9 yet. I want to review everything first.
```

### Follow-up prompts

#### Follow-up 1

```text
Before we move on to Problem 9, I want to fix one issue with how New Chat works.

Right now, clicking New Chat clears the messages on the screen, but the assistant still uses the last 20 saved messages as context. That doesn't really make sense to me. If I'm starting a new conversation, I expect it to be a new conversation, not just the old one with the messages hidden.

I'd like us to separate starting a new conversation from deleting conversation history.

When someone clicks New Chat, the assistant should start fresh without automatically using messages from previous conversations. However, those older conversations should still be saved and accessible to the customer.

If someone returns to an older conversation, the assistant should be able to continue that conversation using its relevant history.

Please find the simplest reliable way to do this using our existing database and application structure.

I know the chat_messages table doesn't currently have a conversation ID, so if we genuinely need to make a small database change, that's fine. Just explain what you're changing and why, and make sure we preserve all existing messages and customer accounts.

I also want this to work across devices. If someone starts a new conversation on their computer, they shouldn't have to figure out where that conversation began when they open the website on their phone.

Please make the conversation controls intuitive. Customers should be able to start a new conversation, find an older one, and continue it without accidentally mixing their histories or deleting anything.

Most importantly, make sure conversations stay associated with the correct customer account. Signed-out visitors should still be able to chat without creating saved account history.

Please test starting new conversations, returning to older ones, switching between conversations, refreshing the page, signing out and back in, and accessing the site from another browser session.

Also check that product cards and product-page context still work correctly in both new and restored conversations.

Use a temporary copy of the database for testing whenever possible, and make sure existing seeded messages are preserved if a schema change is needed.

As usual, record this as a follow-up under Problem 8 in AI_prompts.md, update the relevant documentation, and tell me what you changed and what you tested.

Don't start Problem 9 yet. I want to make sure this is working properly first.
```

### What was missing or needed improvement

_(Problem 8)_ The initial implementation treated **New chat** as a screen-only boundary: the saved history stayed one
continuous thread, and the assistant kept using the last 20 saved messages as context, so a "new" chat wasn't really
new. The boundary was also stored per browser, so it didn't carry across devices. Follow-up 1 asked for real,
separate conversations: a fresh start on New chat, older conversations saved and resumable, and the same behavior on
every device.
---

## Problem 9 — Usability and Performance Improvements

### Initial prompt

```text
Okay, Problem 8 is complete, including the changes we made to separate conversations properly. Let's move on to Problem 9 and focus on making the website and shopping assistant easier and more enjoyable to use.
The professor wants two frontend improvements and two backend or AI agent improvements. I'd like these to be meaningful changes that actually improve the customer experience, rather than just adding features for the sake of having them.
We've already identified a few things that could be better, especially how long some chatbot responses take and how the assistant occasionally performs unnecessary product searches.
For the frontend, I'd like us to focus on two areas:
1. Make the chat experience better while customers are waiting.
Some of the more complicated product searches are taking 6–12 seconds, which can feel like a long time when you're waiting for a response.
I'd like the chat to give customers better feedback about what's happening, so it doesn't feel like the assistant has frozen.
We already have a typing indicator, but I think we can make that more informative. For example, if the assistant is looking through products or checking inventory, it could display a helpful status message rather than just saying "Typing."
Please keep this accurate. I don't want the interface claiming it's checking inventory unless that's actually happening.
2. Make previous conversations easier to navigate.
We just added separate conversations and a Chats menu in Problem 8. I'd like to make that experience more intuitive.
Right now, conversation titles are based on the first message, which means a lot of them could end up named things like "Hi" or "Hello."
I'd like customers to be able to identify their previous conversations more easily. Consider improving how chats are titled or organized, and make sure switching between them feels straightforward.
If allowing customers to rename conversations is the simplest useful improvement, that's fine too.
For the backend and AI agent, I'd like us to focus on two areas:
3. Reduce unnecessary database searches and tool calls.
Claude previously noticed that the assistant sometimes searches the catalogue after simple messages like "Thanks."
That doesn't make sense, and it adds unnecessary waiting time and API usage.
I'd like the assistant to recognize when it actually needs product information and when it can simply respond conversationally.
However, accuracy is still the priority. If someone asks about a product, price, size, or inventory, the assistant should continue checking the database rather than relying on memory or guessing.
4. Improve response efficiency without sacrificing accuracy.
Some product recommendations take 6–12 seconds because the assistant searches products, checks stock, and then generates its response.
Please investigate whether there are reasonable ways to make that process faster.
I'm not asking you to rebuild the agent or remove important verification steps. I'd rather have accurate results that take a few extra seconds than fast answers that are wrong.
Look for opportunities to reduce redundant work, unnecessary model calls, or inefficient database operations while preserving the safeguards we already implemented.
Before making changes:
Please inspect the current implementation and run a few representative tests to establish how the website and assistant perform now.
If one of my suggested improvements would require major architectural changes or create unnecessary risks, explain that and propose a simpler alternative.
We have already completed most of the assignment, so I don't want to introduce a bunch of new problems this late in development.
Testing:
After implementing the improvements, please test them through the actual website.
In particular, I'd like you to verify that:

* Customers receive useful, accurate feedback while waiting for AI responses.
* The chat remains usable on desktop and mobile.
* Previous conversations are easier to identify and navigate.
* Basic greetings and acknowledgments don't trigger unnecessary product searches.
* Product questions still trigger the necessary database lookups.
* Product cards continue to display accurate information.
* Size availability and prices still match the database.
* Response times are compared with our original measurements.
* Switching conversations doesn't mix customer histories.
* Existing account functionality, product pages, and chat memory still work.

Please measure improvements where possible rather than just assuming the changes helped.
If the response times don't meaningfully improve, explain what you tried and why rather than claiming success.
Documentation:
Continue maintaining AI_prompts.md with my actual prompts and any follow-up requests.
Update `output/usability.md` with four clearly labeled improvements: two frontend and two backend/agent.
For each improvement, explain what the issue was, what you changed, why you chose that approach, and what testing demonstrated.
Update `output/harness.md` and `output/design.md` wherever the changes affect the application architecture or behavior.
Keep all existing documentation intact.
When you're finished, give me a summary of the four improvements, the before-and-after testing results, and anything we should still consider improving.
Don't move on to Problem 10 yet. I want to review these changes first.
```

### Follow-up prompts

#### Follow-up 1

```text
Try again
```

_(Sent while the baseline benchmark was running, after a burst of failed requests caused by a brief network outage.
The assistant reran the measurement.)_

#### Follow-up 2

```text
Try again
```

_(Sent after the final Problem 9 summary. The assistant re-checked that the app and documentation were in place and
resent the summary.)_

### What was missing or needed improvement

_Nothing recorded yet._
---

## Problem 10 — Visual Design and Handsome Dan

### Initial prompt

```text
okay so for 10 are you able to locate the Handsome Dan animations that we designed a few weeks ago?
```

### Follow-up prompts

#### Follow-up 1

```text
Okay, let's move on to Problem 10 and focus on the overall design and personality of the Campus Customs website!
This is the part I've been looking forward to because I already created a bunch of animated Handsome Dan assets for my previous AI Foundations assignment. I originally thought that project would need a frontend, and it didn't, so I'm excited that we can finally put those designs to use.
I want Campus Customs to feel like a real, polished Yale-inspired clothing store, but I also want it to have some personality. I don't want a generic e-commerce template with a chatbot stuck in the corner. I'd like Handsome Dan to feel like he's actually part of the shopping experience.
We've already completed the major functionality through Problem 9, so this should primarily be a visual design and animation project. I don't want to rebuild anything that's already working.
1. Use the Handsome Dan assets we already have
You've inspected the existing files, so let's build on what you found.
We have:

* A six-frame running animation.
* A six-frame sniff-walking animation.
* Individual poses including neutral, sitting, sniffing, fetching, found it, and the cookie pop-up.
* A paw print, Yale Y cookie, and Y crest.
* The original reference sheet and the animation preview we previously selected.

Please use the finished animation frames, strips, and poses rather than the earlier experimental versions.
I want Dan to look consistent throughout the website, so don't mix in unrelated mascot designs or create completely new versions of him.
Also, remember that the animation frames have transparent backgrounds, but several individual poses still have cream-colored backgrounds. Please account for that in the design rather than leaving obvious rectangular backgrounds against Yale blue.
The individual poses are relatively small, so don't enlarge them so much that they become blurry.
2. Give Handsome Dan different behaviors in the shopping assistant
This is the feature I'm most excited about.
I want Dan's animations to correspond to what the AI shopping assistant is actually doing.
Here's what I'm imagining:
Neutral or sitting Dan: When the assistant is idle, greeting someone, or having a normal conversation.
Sniff-walking Dan: When the assistant is actually searching the catalogue or checking inventory. He's sniffing around to find what the customer needs.
Running or fetching Dan: When the assistant is retrieving or preparing product recommendations.
Cookie pop-up or found-it Dan: When the assistant successfully finds products and presents recommendations.
We already added real-time progress updates in Problem 9. Please connect these animation states to those actual events wherever possible.
I don't want fake progress animations. If the assistant is simply answering "Thanks!" it shouldn't look like Dan is searching through inventory.
If the existing backend events don't distinguish between searching and fetching, please use the states we can verify rather than inventing activity.
The cookie animation should be a little celebratory moment when the assistant finds something, not something that plays after every single reply.
I'd like the transitions to feel smooth and natural. Avoid flickering, abrupt changes, or animations restarting repeatedly.
Please also keep the status text alongside the animations so customers can still understand what's happening without having to interpret Dan's behavior.
3. Incorporate Handsome Dan into the rest of the website
I don't want Dan limited to the chatbot. I'd like him to be part of the overall Campus Customs identity.
Please find tasteful ways to use the existing assets in places such as:

* The homepage hero or welcome section.
* The chat launcher and chat header.
* Appropriate decorative elements throughout the website.
* Small details using the paw print, cookie, or crest.

You don't need to use every asset or put Dan on every page. I'd rather have a few really good placements than make the website feel overcrowded.
The product photography should still be the focus of the shopping experience.
If an asset doesn't fit naturally in a particular location, don't force it.
4. Polish the overall website design
Beyond Handsome Dan, I want the entire website to feel cohesive and professionally designed.
Let's continue using Yale blue as the primary color, with white and complementary neutral colors.
Please review the existing homepage, product catalogue, product detail pages, account pages, and chat interface.
Look for opportunities to improve:

* Typography and visual hierarchy.
* Spacing and alignment.
* Navigation and page consistency.
* Product card presentation.
* Buttons, forms, and interactive elements.
* The overall relationship between the storefront and the shopping assistant.

I'd like it to feel like an actual clothing retailer, not a school project, while still retaining some playful personality.
That said, I don't want a completely new design direction. Build on what we've already created.
Keep the product images prominent and avoid adding unnecessary decorations that compete with them.
5. Make sure the design works on different screen sizes
The website should look polished on desktop, tablet, and mobile.
Please pay particular attention to the chatbot because the animations and product cards could make it feel crowded on smaller screens.
Make sure:

* Animations don't overlap text, buttons, or product cards.
* The chat remains easy to open, close, and navigate.
* Product images retain their correct proportions.
* The navigation remains intuitive.
* Nothing gets cut off or creates horizontal scrolling.
* Text and buttons remain readable and accessible.

Please also respect reduced-motion preferences. If someone has animations disabled, use an appropriate static Handsome Dan pose instead.
If an animation fails to load, the interface should still work normally.
I want the animations to add personality without making the site slower or harder to use.
6. Preserve everything we've already built
We've spent a lot of time getting the actual shopping experience working, so please avoid changing backend behavior unless there's a genuine reason.
The following features should continue working exactly as expected:

* Product browsing and filtering.
* Individual product pages.
* Customer registration, login, and logout.
* The PydanticAI shopping assistant.
* Database product and inventory lookups.
* Clickable product recommendation cards.
* Saved customer conversations.
* Separate conversation histories.
* Product-page awareness.
* The progress indicators and performance improvements from Problem 9.

If the visual changes require modifying any of these components, please be careful not to remove or break existing functionality.
Also, don't add shopping-cart or checkout features. Those aren't part of the assignment, and we shouldn't suggest customers can use features that don't exist.
7. Review the design before making major changes
Since you already inspected the Handsome Dan assets, I'd like you to briefly explain your proposed placements and animation states before implementing them.
You don't need to stop for approval unless you encounter a major design decision or something that could substantially change the website.
Otherwise, use your judgment and proceed with the implementation.
I'd rather see a complete working version that we can review and fine-tune than spend a long time discussing small design decisions before seeing anything.
8. Test the finished website
Once the visual changes are complete, please test everything through the browser.
I'd like you to check:

* The homepage and all major page types.
* Product cards and product detail pages.
* Account creation and login.
* The shopping assistant and its different animation states.
* Actual catalogue and inventory searches.
* Product recommendation cards.
* Switching between saved conversations.
* The website on desktop and mobile.
* Reduced-motion behavior.
* Missing or failed animation assets.
* Any visual issues caused by the new design.

Please verify that Dan's animations correspond to actual assistant activity rather than just whether the animations technically play.
Also check that the new assets haven't noticeably slowed down the website.
Fix anything that isn't working correctly and retest it.
9. Documentation
Please continue maintaining AI_prompts.md with my actual prompts and any follow-up instructions.
Update output/design.md with the Problem 10 visual design work, including:

* The overall design direction.
* How the Handsome Dan assets were used.
* Where each animation or pose appears.
* How animation states are connected to the assistant's actual behavior.
* Responsive design considerations.
* Accessibility and reduced-motion behavior.
* Any compromises or design decisions we made.
* The results of your visual and functional testing.

Preserve all of the documentation from the earlier problems.
10. Final review
When you're finished, please give me a summary of the changes, identify which Handsome Dan assets were incorporated, and explain how the chatbot animations work.
I'd also like to know whether there were any assets you decided not to use and why.
Please provide the local website address so I can review the design myself.
Don't move on to Problem 11 yet. I want to see the finished website and decide whether we need any visual adjustments before we start the final testing and submission work.
```

### What was missing or needed improvement

- The initial prompt only asked where the Handsome Dan animations were; the full design brief came in Follow-up 1.
- Browser testing caught a few issues that were fixed before handing over:
  - The hero image was lazy-loaded, so it now loads eagerly.
  - The Y cookie icon showed a cream square on a tinted card, so it is now cropped to a circle.
  - The footer's "Ask Handsome Dan" button was covered by the floating chat launcher, so it was removed.
  - The decorative icons had no fallback if an image failed to load, so they now hide themselves.
  - A missing animation strip briefly showed an empty box on each retry, so the failure is now remembered.

## Problem 11 — Comprehensive Application Check

### Initial prompt

```text
Okay, Problem 10 is complete, and I've reviewed the finished website myself. Everything looks great, including the Handsome Dan animations!
Let's move on to Problem 11 and do a comprehensive check of the entire application.
We've been testing individual features throughout the assignment, but now I want to make sure everything works together and that we have clear evidence of the finished website for submission.
The professor wants us to create an HTML testing report at `output/app_check.html`, including screenshots showing the application and its functionality.
I don't want this to be a generic report that just says everything works. I want it to show what was actually tested, what happened, and how we know the results are correct.
1. Test the complete shopping experience
Please use the actual website in a browser and test it the way a customer would.
Make sure the homepage, product catalogue, filters, navigation, and individual product pages all work properly.
Verify that the product information, prices, images, and inventory are coming from the database and are accurate.
Also check that the website works on desktop and mobile.
2. Test customer accounts
Please verify that customers can register, log in, stay logged in, and log out.
Check that the professor's existing test account still works and that new accounts can be created successfully.
Also verify that different customers can't access each other's account information or conversation history.
Use temporary database copies for tests that would create accounts or change conversation history. I don't want the test evidence process filling our actual database with fake customers or conversations.
3. Test the AI shopping assistant
I want to make sure Handsome Dan actually works as a shopping assistant, not just that the chat window opens.
Please test:

* Normal conversation and greetings.
* Searching for different types of merchandise.
* Questions about product prices and descriptions.
* Size availability and sold-out products.
* Requests that don't have matching products.
* Clickable product recommendations.
* Follow-up questions about previous recommendations.
* Questions about the product currently being viewed.
* Starting a new conversation.
* Reopening and continuing older conversations.
* Logging out and back in to restore saved history.

Please verify the assistant's product answers against the database and confirm that recommendation cards contain accurate product information.
I also want to know whether its answers are appropriate when it can't verify something. It shouldn't invent stock, policies, or products.
4. Test Handsome Dan's animations
Since we put so much effort into this part, I want to make sure the animations are represented in the final testing evidence.
Please verify that:

* Dan appears correctly throughout the website.
* The sniff-walking animation corresponds to actual catalogue or inventory searches.
* The running animation corresponds to the appropriate agent activity.
* The cookie pop-up only appears when actual product recommendations are returned.
* Ordinary conversations don't trigger fake searching animations.
* The animations work on desktop and mobile.
* Reduced-motion preferences are respected.

Please capture screenshots of the different Dan states where possible. If a state is too brief to capture reliably, use an actual recorded event or other reproducible evidence rather than fabricating a screenshot.
5. Create the HTML testing report
Please create `output/app_check.html` as a self-contained, well-organized report of the finished application.
I'd like it to include:

* A brief description of Campus Customs and the AI shopping assistant.
* The test environment and how the application was started.
* Screenshots of the homepage and product catalogue.
* A product detail page showing real inventory.
* The registration and login interfaces.
* The chatbot displaying a real AI-generated response.
* Product cards returned through the assistant.
* Saved conversation history.
* Handsome Dan's visual design and animations.
* Mobile screenshots demonstrating responsive behavior.
* A summary of the test results, including anything that didn't work or required correction.

Please place the screenshot files in `output/app_check_images/` and reference them using relative paths so the report can be opened locally and displayed correctly from GitHub.
Make the report visually organized and easy for the professor to review. I don't want someone to have to search through a wall of text to figure out what was tested.
Please don't include passwords, API keys, session cookies, private customer information, or other sensitive information in screenshots or documentation.
If the provided database contains personal-looking information, use safe test data or redact identifying details before including evidence.
6. Verify reliability and security
Please also check that:

* The application handles invalid inputs and unavailable products appropriately.
* Customer sessions and conversation history remain isolated.
* The chatbot doesn't reveal its private instructions or credentials.
* Product cards and inventory claims are verified against the database.
* The frontend build and relevant backend tests pass.
* The application behaves reasonably if the AI provider is temporarily unavailable.
* None of the recent visual changes broke earlier functionality.

Please avoid sending unnecessary repeated requests to Portkey just to produce screenshots. Reuse valid evidence where possible, but don't present previous results as though they were newly tested.
7. Final documentation
Continue maintaining `AI_prompts.md` with my actual prompts and any necessary follow-up requests.
Update the relevant documentation to explain the testing process, any problems discovered, and any fixes made.
Preserve the documentation from Problems 1–10.
If something doesn't work, fix it when reasonable, retest it, and document the correction. If it can't be fixed without major changes, explain the limitation clearly rather than hiding it.
8. Completion report
When you're finished, please tell me:

* How many tests were performed and how many passed.
* Which screenshots were captured.
* Where I can open the completed HTML report.
* Whether you discovered and corrected any issues.
* Whether any functionality remains incomplete.
* Whether the application is ready for the final audit and GitHub submission.

Don't move on to Problem 12 yet. I want to review the testing report first.
```

### Follow-up prompts

_None yet._

### What was missing or needed improvement

- The check found two visual problems from Problem 10, and both were fixed and retested:
  - The signed-in chat header was cramped: "Handsome Dan" plus the Chats and New chat buttons wrapped the title.
  - On phones, Dan's head was cut off in the sniff and run animation.
- Three problems in the new test scripts themselves were corrected:
  - One check expected the wrong wording.
  - The credential-leak check gave a false positive.
  - Requests to `localhost` were slow on Windows.
- A blunt prompt-injection test was stopped by the provider's content filter, so two milder probes were added to test
  the model itself.
## Problem 12 — Audit Trail, AI Safety and Documentation

### Initial prompt

```text
Okay, Problem 11 is complete, and all 222 checks passed! Let's move on to Problem 12 and focus on the audit trail, AI safety, and making sure everything is properly documented.
We're almost finished with the assignment, so I don't want to make unnecessary changes to the application at this point. I mainly want to verify that what we've built is reliable, safe, and properly documented.
I also want the audit trail to reflect what the assistant actually does, rather than just generating example records that look convincing.
1. Create the AI audit trail
The professor requires an audit trail in `output/audit_trail.json`.
Please review our existing PydanticAI agent, tools, and FastAPI chat endpoints to determine what activity we're already recording and what additional information we need.
I want us to be able to trace important AI interactions, including:

* When a customer sends a message.
* Which tools the assistant uses.
* Which products or inventory records are retrieved.
* Whether product recommendations were verified against the database.
* Whether a request succeeds, fails, or is blocked.
* Relevant timestamps, durations, and errors.

Please make sure the records are structured, consistent, and easy to understand.
Use actual application events and tool calls. Don't invent successful requests or create fictional records just to fill the audit file.
I'd also like the logging to be useful for troubleshooting, so we can distinguish an AI provider issue from a database problem or an application error.
The audit trail should persist appropriately rather than disappearing whenever the server restarts.
2. Protect customer information
Because this project includes account information and saved conversations, I want to be careful about what gets recorded.
Please don't write passwords, API keys, session cookies, authentication tokens, or other credentials into the audit trail.
Avoid storing full customer messages or personally identifiable information unless the assignment specifically requires it.
If an audit record needs to identify an interaction, use an appropriate request identifier or anonymized reference rather than exposing the customer's account details.
Please also review the existing logs to make sure sensitive information isn't being printed elsewhere.
3. Review the assistant's safety rules
I want Handsome Dan to stay focused on helping customers shop for Campus Customs merchandise.
Please review the existing system prompt and agent behavior to confirm that the assistant:

* Uses the database rather than inventing prices, inventory, or products.
* Doesn't claim unavailable sizes are in stock.
* Doesn't invent discounts, shipping policies, returns policies, or checkout capabilities.
* Doesn't expose system instructions or API credentials.
* Handles suspicious or manipulative requests appropriately.
* Doesn't trust instructions embedded in product descriptions or other database content.
* Handles missing products, invalid inputs, and unavailable services gracefully.
* Keeps customer conversations and account information separate.

We already implemented several of these protections in earlier problems, so please verify and document them rather than rebuilding everything unnecessarily.
If you identify a meaningful vulnerability, explain it and implement a targeted correction. Avoid major architectural changes this close to submission unless they're necessary.
4. Test the audit trail
Please run a small set of actual interactions through the application and confirm that the audit trail captures them accurately.
I'd like the tests to include:

1. A normal greeting that doesn't require product tools.
2. A product search that returns recommendations.
3. A size or inventory question.
4. A request for a nonexistent product.
5. A sold-out size.
6. An invalid or suspicious request.
7. An AI provider failure or timeout, simulated safely where possible.
8. A request from a signed-in customer, ensuring the audit trail doesn't expose their identity or credentials.

Verify that the recorded tool calls correspond to what actually happened.
Please also test that the audit records remain readable after the server restarts.
Use a temporary database copy and safe test credentials wherever possible.
If we need representative records in `output/audit_trail.json` for submission, generate them from these actual test interactions. Clearly distinguish that captured test evidence from any ongoing local audit log.
5. Review the documentation and public files
Before we publish this project, please review everything that would eventually be included in the GitHub repository.
Check for:

* API keys, passwords, session secrets, and other credentials.
* Personal customer information in documentation or screenshots.
* Accidentally included database files or product image directories.
* Temporary files, backups, caches, or generated content that shouldn't be public.
* Broken documentation links or missing required files.
* Any inconsistencies between the README and the way the application actually runs.

From Problem 11, we also identified an example email in `output/design.md`. Please replace `Kate@yale.edu` with a generic placeholder.
The professor requested screenshot evidence, so product photographs appearing within screenshots are acceptable unless the assignment explicitly prohibits them. Keep the original product image directory excluded from GitHub.
Make sure that `AI_prompts.md` still accurately represents our actual prompting history. Don't rewrite earlier prompts to make them sound better or invent missing interactions.
6. Technical documentation
Please update `output/harness.md` to explain:

* How the audit trail is generated and stored.
* What events are recorded.
* How sensitive information is protected.
* What safety rules the assistant follows.
* How product information is verified.
* How errors and provider failures are handled.
* Any important limitations or remaining risks.

Also update other relevant documentation as needed, preserving the work we've already completed.
7. Final verification
After the audit work, please run the necessary regression tests to confirm that nothing important was broken.
I want the storefront, customer accounts, AI shopping assistant, database tools, product recommendations, saved conversations, and Handsome Dan animations to continue working.
Please validate that `output/audit_trail.json` contains properly structured JSON and actual audit evidence.
If something fails, investigate, fix it when appropriate, and retest.
8. Completion report
When you're finished, tell me:

* What audit logging was implemented.
* What information is included in each audit record.
* How sensitive information is protected.
* What safety testing was performed.
* Whether any vulnerabilities or issues were discovered.
* Whether anything was changed or fixed.
* Whether all required documentation is complete.
* Whether the project is ready for public GitHub submission.

Please clearly identify any remaining limitations rather than claiming the system is perfectly secure.
As always, record my actual prompt and any follow-up requests in `AI_prompts.md`.
Don't start Problem 13 or publish anything to GitHub yet. I want to review the audit results before we submit.
```

### Follow-up prompts

_None yet._

### What was missing or needed improvement

- The safety review found two prompt-injection gaps:
  - Instructions planted in database text weren't covered by the prompt.
  - The customer's registered first name was placed in the assistant's context unfiltered.
- The model ignored both planted instructions before the fix. Because that was one trial each, a prompt rule and a
  first-name filter were added, and the tests were re-run with the same correct result.
- One console log line printed a customer id; it now prints the request id.
- The blunt "suspicious request" test was stopped by the provider's content filter. The model's own refusals had already
  been tested in Problem 11 (turns #18–19).

## Problem 13 — GitHub Repository and Final Submission

### Initial prompt

```text
Okay, we've officially completed Problems 1–12, and all of our testing and security checks have passed! Let's finish Homework 4 by preparing the Campus Customs project for GitHub and final submission.
I want the finished repository to be organized, professional, and easy for my professor to review. We've put a lot of work into this website, and I'd like the submission to reflect that.
The actual application is complete, so please don't make unnecessary changes to the functionality or visual design at this point.
1. Final project organization
Before publishing anything, review the complete `hw4` project structure and make sure everything is organized correctly.
Please check that all required files and deliverables from Problems 1–12 are included, especially:

* `AI_prompts.md`
* `README.md`
* `requirements.txt`
* `.gitignore`
* `.env.example`
* The React/Vite frontend and its package files
* The FastAPI backend
* The PydanticAI agent, tools, models, and system prompt
* `output/harness.md`
* `output/design.md`
* `output/usability.md`
* `output/app_check.html`
* `output/app_check_images/`
* `output/audit_trail.json`
* Any necessary application tests and supporting source files

If a file is missing or incomplete, investigate before making changes.
Don't create fake content just to make the repository appear complete.
2. Make the README useful
I want someone reviewing the repository to understand what Campus Customs is, what we built, and how the application works.
Please make sure the README clearly explains:

* The purpose of the Campus Customs project.
* The main website and AI shopping assistant features.
* The technologies used, including React, FastAPI, PydanticAI, SQLite, and Portkey.
* The project directory structure.
* How to install dependencies and run the frontend and backend locally.
* How to configure environment variables without exposing credentials.
* Where the SQLite database and product images should be placed.
* How the database's one-time conversation migration works.
* How to access the application locally.
* Where to find the testing evidence and other required documentation.
* Any important limitations, including the fact that this is a course project without a functioning checkout.

Please make sure the startup instructions are accurate and reflect how we've actually been running the application.
Since the original database and product images won't be published, explain that those files must be supplied locally. Don't suggest the application will work with real products without them.
3. Final security check before publishing
This repository will be public, so I want one last thorough review of exactly what Git is going to upload.
Please verify that we're not accidentally publishing:

* API keys or provider credentials.
* The real `.env` file.
* Session secrets, authentication tokens, or cookies.
* The original SQLite database or any database backups.
* The original product images.
* The live customer audit log.
* Virtual environments, node_modules, caches, or temporary files.
* Customer passwords, password hashes, or private account information.
* Sensitive information in screenshots, documentation, or test output.

We already completed a security audit in Problem 12, but please verify the actual staged Git contents again rather than relying only on `.gitignore`.
Also check that no secrets appear in any commits before publication.
Please preserve `AI_prompts.md` as an accurate record of what I actually submitted to Claude, while keeping genuine passwords, API keys, and other secrets redacted.
The screenshots in `app_check_images/` are required evidence of the application. They can include product photography displayed within the website, but please make sure they don't expose private customer information or credentials.
4. Prepare the GitHub repository
Use the GitHub CLI that we already configured and authenticated.
Create a public GitHub repository for Homework 4 using a clear, professional name such as `campus-customs-ai-shopping-assistant`, unless a repository for this project already exists.
Before creating anything, check that we're not duplicating an existing repository or overwriting another project.
Use `main` as the default branch.
Commit the source code, documentation, required screenshots, and test evidence.
Do not commit excluded data, secrets, unnecessary generated files, or files belonging to other homework assignments.
Please use a clear initial commit message.
If the professor's instructions specify a particular repository name, visibility setting, or submission structure, those requirements take priority over my suggested name.
5. Verify the published repository
After pushing the project, please verify the actual GitHub repository, not just the local files.
Confirm that:

* The repository is public.
* The main branch contains the expected project files.
* The README displays properly.
* `AI_prompts.md` is accessible.
* The documentation files are present.
* `output/app_check.html` and its screenshots are included.
* `output/audit_trail.json` is valid JSON and accessible.
* The application source code is included.
* No excluded database, image directory, environment file, or credentials were uploaded.
* Git reports a clean working tree after the commit.

Please also check the relative links in the README and documentation.
If GitHub cannot display the full HTML testing report directly, that's fine, but make sure the file and its supporting images are available for someone to download and open locally.
6. Final assignment review
Before calling the assignment complete, please go back through Problems 1–13 and verify that we've addressed the requirements and produced the expected deliverables.
I want a concise checklist identifying which problem requirements are satisfied and where the supporting files or evidence can be found.
If there's something we didn't actually implement or couldn't verify, please tell me rather than claiming the assignment is perfect.
Don't make major changes at this stage unless they're needed to satisfy an explicit assignment requirement or correct a serious issue.
7. Final documentation and completion report
As always, record this prompt accurately under Problem 13 in `AI_prompts.md` before committing.
If any follow-up prompts are needed during the final submission process, document those as well.
When everything is finished, please give me:

* The public GitHub repository URL.
* Confirmation that the files were successfully pushed.
* The final commit identifier.
* A summary of the repository contents.
* The results of the final security check.
* A checklist showing all 13 problems and their completion status.
* Any remaining limitations or concerns.
* Clear instructions for what I need to submit to my professor.

Please don't claim that the submission is complete until you've verified the public repository is accessible and contains the necessary files.
And please don't submit anything to Yale's course platform on my behalf. I'll handle that final step myself.
```

### Follow-up prompts

_None yet._

### What was missing or needed improvement

- The professor's Homework 4 instructions weren't available as a file, so the suggested repository name
  `campus-customs-ai-shopping-assistant` (public, `main` branch) was used. No existing repository had that name.
- The README was rewritten from a problem-by-problem changelog into a reviewer's guide: purpose, features, technology,
  structure, local data and migration, configuration, setup, running, evidence and limitations.
- The final scan of the staged files flagged three items, all checked and found not to be secrets:
  - the `.env.example` placeholder;
  - a deliberately fake cookie in a test;
  - an example address quoted in the Problem 12 prompt, kept verbatim.
