package expo.modules.banksms

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Log
import com.facebook.react.HeadlessJsTaskService

/**
 * Gets every incoming SMS (the app may be closed). Only Federal Bank debit alerts are passed on, to the JS
 * task that sends them to the backend; every other SMS is ignored here and never leaves the phone.
 */
class BankSmsReceiver : BroadcastReceiver() {
  override fun onReceive(context: Context, intent: Intent) {
    if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return
    val parts = Telephony.Sms.Intents.getMessagesFromIntent(intent) ?: return
    // A long SMS arrives in several parts
    val text = parts.joinToString("") { it.messageBody ?: "" }
    if (!isBankDebit(text)) return

    Log.i(TAG, "Federal Bank debit SMS received, passing it to the app")
    val task = Intent(context, BankSmsTaskService::class.java).putExtra("text", text)
    try {
      context.startService(task)
      HeadlessJsTaskService.acquireWakeLockNow(context)
    } catch (e: Exception) {
      Log.w(TAG, "Couldn't start the SMS task", e)
    }
  }

  companion object {
    private const val TAG = "TaskMonBankSms"

    /** Same check as the backend's parser, kept loose: the backend reads the details. */
    fun isBankDebit(text: String) = text.trimStart().startsWith("Debited") && text.contains("Federal Bank")
  }
}
