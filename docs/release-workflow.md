## Mobile App Release Workflow

%%{init: {'flowchart': {'nodeSpacing': 50, 'rankSpacing': 70}}}%%
flowchart TB

subgraph CI["CI Cut-off (Friday Morning)"]
    A[CI Trigger] --> B[Jira<br/>Create Release Candidates]
    B --> C[Slack #app-release<br/>Notify Stakeholders]
end

subgraph IOS["iOS Release Candidate"]
    D1[Fetch Latest Build]
    D1 --> D2[Jira Version<br/>2.YYYYWW.0]
    D2 --> D3[Automation Tests]
    D3 --> D4[App Store Connect<br/>Draft]
    D4 --> D5[Marketing Updates]
    D5 --> D6[Submit for Review]
end

subgraph ANDROID["Android Release Candidate"]
    E1[Fetch Latest Build]
    E1 --> E2[Jira Version<br/>3.YYYYWW.0]
    E2 --> E3[Automation Tests]
    E3 --> E4[Google Play<br/>Draft]
    E4 --> E5[Marketing Updates]
    E5 --> E6[Submit for Review]
end

subgraph MONDAY_IOS["Monday iOS Release"]
    F1[Verify Readiness]
    F1 --> F2[Approval & Regression]
    F2 --> F3[Test Report]
    F3 --> F4[Attach to Jira]
    F4 --> F5[7-Day Rollout]
end

subgraph MONDAY_ANDROID["Monday Android Release"]
    G1[Verify Readiness]
    G1 --> G2[Approval & Regression]
    G2 --> G3[Test Report]
    G3 --> G4[Attach to Jira]
    G4 --> G5[10% → 25% → 50% → 75% → 100%]
end

C --> D1
C --> E1
D6 --> F1
E6 --> G1

