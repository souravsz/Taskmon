package expo.modules.banksms

import android.content.Intent
import com.facebook.react.HeadlessJsTaskService
import com.facebook.react.bridge.Arguments
import com.facebook.react.jstasks.HeadlessJsTaskConfig

/** Starts the app's JS (without showing it) to run the "TaskMonBankSms" task with the SMS text. */
class BankSmsTaskService : HeadlessJsTaskService() {
  override fun getTaskConfig(intent: Intent?): HeadlessJsTaskConfig? {
    val extras = intent?.extras ?: return null
    return HeadlessJsTaskConfig(
      "TaskMonBankSms",
      Arguments.fromBundle(extras),
      30_000, // ms: enough to send one request to the backend
      true, // also run while the app is open
    )
  }
}
