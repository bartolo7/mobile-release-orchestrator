## Mobile App Release Workflow


```mermaid
flowchart TB
    %% ===== CI CUT-OFF =====
    A[Continues Integration <br/>Cut-off Trigger<br/>Friday Morning] --> B[JIRA<br/>Create iOS & Android Release Candidates]
  
    %% ===== PARALLEL BUILDS =====
    B --> D1[iOS Build]
    B --> D2[Android Build]

    %% ===== iOS RC =====
    D1 --> I1[Fetch Latest Successful iOS Build]
    I1 --> I2[Create Jira Version<br/>2.YYYYWW.0]
    I2 --> I3[Trigger Automation Regression Tests]
    I3 --> I4[App Store Connect<br/>Create Draft Version]
    I4 --> I5[Marketing Updates<br/>Screenshots & Metadata]
    I5 --> I6[Submit for Review<br/>24h Weekend Review]
    I6 --> I7[Slack Notification<br/>iOS RC Submitted]

    %% ===== Android RC =====
    D2 --> A1[Fetch Latest Successful Android Build]
    A1 --> A2[Create Jira Version<br/>3.YYYYWW.0]
    A2 --> A3[Trigger Automation Regression Tests]
    A3 --> A4[Google Play<br/>Create Draft Version]
    A4 --> A5[Marketing Updates<br/>Screenshots & Metadata]
    A5 --> A6[Submit for Review<br/>24h Weekend Review]
    A6 --> A7[Slack Notification<br/>Android RC Submitted]

    %% ===== MONDAY IOS RELEASE =====
    I6 --> M1[CI Monday Trigger<br/>iOS Release Workflow]
    M1 --> M2[Verify iOS Ready for Release]
    M2 --> M3[Approval Step<br/>Verify Regression]
    M3 --> M4[Generate Test Report]
    M4 --> M5[Attach Test Report<br/>to Jira Release]
    M5 --> M6[iOS Production Rollout<br/>7 Days]

    %% ===== MONDAY ANDROID RELEASE =====
    A6 --> N1[CI Monday Trigger<br/>Android Release Workflow]
    N1 --> N2[Verify Android Ready for Release]
    N2 --> N3[Approval Step<br/>Verify Regression]
    N3 --> N4[Generate Test Report]
    N4 --> N5[Attach Test Report<br/>to Jira Release]
    N5 --> N6[Google Play Staged Rollout via API]
    N6 --> N7[10% → 25% → 50% → 75% → 100%]
...