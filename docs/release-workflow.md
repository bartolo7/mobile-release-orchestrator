## Mobile App Release Workflow


```mermaid
flowchart TB
    %% ===== CI CUT-OFF =====
    A[Continues Integration <br/>Cut-off <br/>Friday Morning] --> B[JIRA Release<br/>Create iOS & Android Release Candidates]
  
    %% ===== PARALLEL BUILDS =====
    B --> D1[iOS Build]
    B --> D2[Android Build]

    %% ===== iOS RC =====
    D1 --> I1[Fetch Latest Successful iOS Build in CI]
    I1 --> I2[Create Jira Version<br/>2.YYYYWW.0]
    I2 --> I3[Trigger Automation Regression Tests]
    I3 --> I4[AppStoreConnect<br/>Create Draft Version]
    I4 --> I5[Inform Marketing<br/>Screenshots & Metadata]
    I5 --> I6[AppStoreConnect Submit for Review<br/>24h Weekend Review]
    I6 --> I7[Slack Notification to Engineering<br/>iOS Version Submitted]

    %% ===== Android RC =====
    D2 --> A1[Fetch Latest Successful Android Build in CI]
    A1 --> A2[Create Jira Version<br/>3.YYYYWW.0]
    A2 --> A3[Trigger Automation Regression Tests]
    A3 --> A4[Google Play<br/>Create Draft Version]
    A4 --> A5[Inform Marketing <br/>Screenshots & Metadata]
    A5 --> A6[Google Play Submit for Review<br/>24h Weekend Review]
    A6 --> A7[Slack Notification Engineering<br/>Android Version Submitted]

    %% ===== MONDAY IOS RELEASE =====
    I6 --> M1[Continues Integration Monday <br/>iOS Release Workflow]
    M1 --> M2[Verify iOS Ready for Release]
    M2 --> M3[Approval Step<br/>Verify Regression]
    M3 --> M4[Generate Test Report]
    M4 --> M5[Attach Test Report to Jira Release<br/>to Jira Release]
    M5 --> M6[iOS Production Roll-out<br/>7 Days]

    %% ===== MONDAY ANDROID RELEASE =====
    A6 --> N1[CI Monday Trigger<br/>Android Release Workflow]
    N1 --> N2[Verify Android Ready for Release]
    N2 --> N3[Approval Step<br/>Verify Regression]
    N3 --> N4[Generate Test Report]
    N4 --> N5[Attach Test Report to Jira Release<br/>to Jira Release]
    N5 --> N6[Google Play Phase Roll-out via API]
    N6 --> N7[Update the roll-out automtically from 10% → 25% → 50% → 75% → 100%]
