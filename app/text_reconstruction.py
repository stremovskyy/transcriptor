import traceback

from logging import getLogger
logger = getLogger(__name__)


class TextReconstructionService:
    @staticmethod
    def reconstruct_text(transcription, template, model, tokenizer, max_length=1500):
        try:
            # If template is provided, use it directly
            if template:
                prompt_content = template.replace("{transcription}", transcription)
            # Otherwise, determine language and use appropriate default template
            else:
                # Simple language detection based on common characters
                # This is a basic approach - for production, consider using a proper language detection library
                if any(c in transcription for c in 'їєіґ'):
                    # Ukrainian default template
                    prompt_content = (
                        f"Виправте помилки в тексті отриманому зі STT (Whisper) Українською мовою.\n"
                        f"Виправляйте очевидні помилки розпізнавання мовлення. Не додавайте форматування, коментарів чи додаткової інформації.\n"
                        f"STT текст для виправлення:\n{transcription}\n\n"
                        f"Результат має містити ВИКЛЮЧНО виправлений текст без будь-яких додатків."
                    )
                else:
                    # English default template
                    prompt_content = (
                        f"Fix errors in the text obtained from STT (Whisper).\n"
                        f"Correct obvious speech recognition errors. Do not add formatting, comments, or additional information.\n"
                        f"STT text to fix:\n{transcription}\n\n"
                        f"The result should contain ONLY the corrected text without any additions."
                    )

            messages = [{
                "role": "user",
                "content": prompt_content
            }]
            prompt = tokenizer.apply_chat_template(messages, tokenize=False)

            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            input_length = inputs.input_ids.shape[1]

            # Generate text
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=max_length,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                repetition_penalty=1.1,
            )

            # Extract only new tokens
            generated_ids = outputs[:, input_length:]
            reconstructed_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

            return {
                "original_transcription": transcription,
                "template": template,
                "reconstructed_text": reconstructed_text.strip()
            }

        except Exception as e:
            logger.error(f"Text reconstruction error: {e}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Text reconstruction failed: {e}")


def logging_callback(step, token_id, scores):
    if step % 10 == 0:
        logger.info(f"Generation step: {step}")
    return False
