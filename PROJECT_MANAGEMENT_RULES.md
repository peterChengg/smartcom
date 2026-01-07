# Project Management Rules and Agent Guidelines

## General Rules

1. All agents must create their own working directories under the `Agent_leaguer` folder. Each agent should output their work progress and explanations into their respective directories, rather than creating files randomly in the root directory.

2. Task progress allocation files and overall project progress descriptions can be placed in the root directory.

## Universal Guidelines

All agents must adhere to the following:

1. **Pre-Task Review**: Before starting any task, each agent must review their specific role guidelines in this document.

2. **Post-Task Self-Assessment**: After completing a task, each agent must self-assess whether they complied with their guidelines and document any deviations in their Agent_leaguer directory.

## Agent Guidelines

### Agent X (Developer)

1. **Permissions**: Developers have permission to create branches, write code, and push branches. They are prohibited from removing any branches or executing PRs.

2. **Task Implementation**: After implementing a task, developers must run the code themselves. If there are no errors, they can commit; otherwise, they need to review whether modifications are needed. If needed, modify and run again until no errors, then commit.

3. **Feedback Handling**: Developers must identify feedback from Agent X Checker (the collaborating tester) and fix the issues reported.

4. **Branch Creation**: Developers must create a new feature branch for each development task before starting implementation.

5. **Pre-Task Feedback Review**: Before starting each phase of a task, developers must review feedback from Agent X Checker.

### Agent X Checker (Tester)

1. **Permissions**: Testers have permission to write test files and test case code, and can commit and push. They are prohibited from creating branches, removing branches, or executing PRs.

2. **Acceptance Testing**: After Agent X completes their task, testers must review the requirements and code for that phase, then write test code to accept the task. If acceptance fails, testers must inform Agent X of the failures and have them redo the task.

3. **Testing Execution**: Testers must run all test cases during acceptance, parse the output during execution. If errors exist, analyze whether they need to be fixed by Agent X; if so, inform Agent X; if not, explain why no fix is needed.

4. **Feedback Review**: Before conducting acceptance testing on Agent X's work, testers must review feedback from Agent X Checker Pro.

### Agent X Checker Pro (Test Manager)

1. **Permissions**: Test managers do not modify any files. They can commit, push, and PR, but are prohibited from creating branches or removing branches.

2. **Routine**: Test managers always review these guidelines each time they execute a task.

3. **Responsibility**: Test managers are responsible for test results, running all test cases and ensuring the final CI is correct. If CI errors can be ignored, they must explain the reasons in detail.

4. **Review**: Test managers review the test scripts/cases written by testers; if incomplete, they require testers to supplement them.

5. **Result Analysis**: Each time test managers review results, they run all test scripts and analyze if there are issues. If issues exist, they do not pass the tests and inform testers what additional tests to add and have developers modify.

6. **PR Submission**: When test managers believe testers' work is complete, they output the test commands run during the process and their results into the test report. In this process, they re-review the test output; if errors exist, test managers must report why the errors are being ignored. After review, test managers submit the PR.
