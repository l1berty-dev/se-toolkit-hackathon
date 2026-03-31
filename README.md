# Lab 9 - Quiz and Hackathon

Lab opens with a quiz and then kicks off the hackathon.

To get the full point for the lab, you need to pass Tasks 1-3 during the lab. 
Tasks 4-5 must be finished by the usual deadline of Thursday 23:59.

Each student builds their own project:
- Go from idea to a deployed product.
- Use agents and LLMs throughout.

----

#### Task 1 (graded by TA after the lab).
Pen and paper quiz.
- closed book, no devices allowed.
- you get random 3 questions from the question bank.
- answer at least 2 out of 3 correctly.

#### Task 2 (approved by TA during the lab).
The project idea must:
- Be something simple to build, clearly useful, and easy to explain;
- Involve backend + db + web dashboard + user-facing agent;
- Not be an LMS (different from the course project), however you can use the course project as the coding base to iterate from.

Define:
- End users of the product
- Which problem your product solves for the end users
- The product idea in one short sentence

The product must have these components each fulfilling a useful function:
- The nanobot agent
- Frontend
- Backend
- Database

> 🟪 **Note**
> `Telegram` bots deployed on a university VM can fail to receive messages when hosted there.

#### Task 3 (approved by TA during the lab).
Produce a plan including:
- prioritized requirements;
- a clear breakdown of requirements into **three product versions.**

About product versions:
- Each product version builds upon the previous.
- Each must be a functioning product in itself.
- Test each version upon completing, before proceeding to the next one.

In the first version, give priority to features that deliver the most value to end users and are easier to implement. 

#### Task 4 (product version 1 approved by TA during the lab).
- Implement the core features outlined in the plan
- Publish all code as a repo on github.
- Dockerize all services.
- Deploy it to be accessible to use.

Version 1 must be shown and approved by the TA during the lab. Product versions 2 and 3 can be done during the lab or after the lab.


#### Task 5.
Submit presentation with five slides:

1. Title:
  - Product title
  - Your name
  - Your university email
  - Your group

2. Context:
  - Your end users
  - The problem of end users you are solving
  - Your solution

3. Implementation:
  - How you built the product

4. Demo:
  - Pre-recorded demo with live commentaries (no longer than 2 minutes)
  - _Note:_ This is the most important part of the presentation.

5. Links:
  - Link and QR code for each of these:
    - The GitHub repo with the product code
    - Deployed product

----

#### Publishing the product code on GitHub

- Publish the product code in a repository on `GitHub`.

  The repository name must be called `se-toolkit-hackathon`.

- Add the MIT license file to make your product open-source.

- Add `README.md` in the product repository.

  `README.md` structure:

  - Product name (as title)

  - One-line description

  - Demo:
    - A couple of relevant screenshots of the product

  - Product context:

    - End users
    - Problem that your product solves for end users
    - Your solution

  - Features:

    - Implemented and not not yet implemented features

  - Usage:

    - Explain how to use your product

  - Deployment:

    - Which OS the VM should run (you may assume `Ubuntu 24.04` like on your university VMs)
    - What should be installed on the VM
    - Step-by-step deployment instructions
