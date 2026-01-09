function processText() {
  let text = document.getElementById("inputText").value;

  // CPF
  text = text.replace(/\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b/g, "[CPF OCULTO]");

  // Email
  text = text.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}/gi, "[EMAIL OCULTO]");

  // Telefone
  text = text.replace(/\b\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b/g, "[TELEFONE OCULTO]");

  // Endereço simples (heurístico)
  text = text.replace(/\b(Rua|Avenida|Av\.|Travessa|Quadra|Condomínio|Conj\.)\s+[\w\s]+/gi, "[ENDEREÇO OCULTO]");

  // Nomes próprios simples (heurística)
  text = text.replace(/\b([A-Z][a-z]+\s[A-Z][a-z]+)\b/g, "[NOME OCULTO]");

  document.getElementById("outputText").innerText = text;
}
