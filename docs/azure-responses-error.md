# Reported Azure Responses resource mismatch

Reported message: “The requested item was created under a different Azure OpenAI resource. Use the same resource that created the item to access it.”

The credential-safe local diagnostic found Codex configured with the `agentrouter` provider, `agentrouter.org` endpoint and the Responses wire API. It did not find the reported mismatch in the inspected local log tail. Credentials were not printed; model, provider, permission settings and authentication files were not modified.

The message says a referenced item is resource-scoped. Resource switching behind the gateway is a likely explanation, but the local evidence does not establish the gateway's routing or prove the cause. Official [conversation-state documentation](https://developers.openai.com/api/docs/guides/conversation-state) describes stored response references and manually supplied conversation context.

If the message returns in Codex, start a fresh conversation instead of resuming the affected response chain. If it recurs in a fresh conversation, the gateway operator needs to verify consistent Azure resource routing for Responses items and continuation. A local restart cannot repair a gateway that routes an item's continuation to another resource. Keep the selected model/provider unless intentionally deciding otherwise.

INHERIA's optional model adapter avoids this class of continuation reference: every call is stateless, uses `store=false`, and sends neither `previous_response_id` nor stored conversation/item references. The stateless payload and unsupported-citation rejection are tested. No live Azure request was used to claim that the upstream Codex error is permanently fixed.

Run `python tools/diagnose_codex.py` from the project root for the read-only metadata report. Run future Codex sessions in a normal project directory to avoid the separate System32 Windows helper failure. Do not weaken sandbox settings or delete session history as a workaround.
