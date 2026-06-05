const API_URL = "http://localhost:5000";

const form = document.getElementById("giftForm");
const resultsSection = document.getElementById("results");
const resultsList = document.getElementById("resultsList");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error");
const categoryGroup = document.getElementById("categoryGroup");

window.addEventListener("DOMContentLoaded", async () => {
    try {
        const res = await fetch(`${API_URL}/categories`);
        const data = await res.json();
        data.categories.forEach(cat => {
            const label = document.createElement("label");
            label.innerHTML = `<input type="checkbox" value="${cat}"> ${cat}`;
            categoryGroup.appendChild(label);
        });
    } catch (err) {
        categoryGroup.innerHTML = `<small>카테고리 로딩 실패 (백엔드 확인 필요)</small>`;
    }
});

form.addEventListener("submit", async (e) => {
    e.preventDefault();  // 페이지 새로고침 방지
    errorBox.classList.add("hidden");
    resultsSection.classList.add("hidden");
    loading.classList.remove("hidden");

    const age = parseInt(document.getElementById("age").value);
    const gender = document.querySelector('input[name="gender"]:checked').value;
    const budget = parseInt(document.getElementById("budget").value);
    const categories = Array.from(
        document.querySelectorAll('#categoryGroup input:checked')
    ).map(cb => cb.value);

    try {
        const response = await fetch(`${API_URL}/recommend`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ age, gender, budget, categories })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || "서버 오류");
        }

        const data = await response.json();
        displayResults(data.recommendations);
    } catch (err) {
        errorBox.textContent = `❌ ${err.message}`;
        errorBox.classList.remove("hidden");
    } finally {
        loading.classList.add("hidden");
    }
});
function displayResults(gifts) {
    resultsList.innerHTML = "";

    if (gifts.length === 0) {
        resultsList.innerHTML = `<div>조건에 맞는 선물을 찾지 못했어요.</div>`;
    } else {
        const emojiMap = {
            "뷰티/케어": "💄", "식품/간식": "🍫", "패션/잡화": "👜",
            "리빙/인테리어": "🏠", "디지털/가전": "📱", "취미/여가": "🎨",
            "상품권": "🎫", "캐릭터/굿즈": "🧸"
        };

        gifts.forEach(gift => {
            const card = document.createElement("div");
            card.className = "gift-card";
            const emoji = emojiMap[gift.category] || "🎁";
            const linkBtn = gift.link 
                ? `<a href="${gift.link}" target="_blank" class="gift-link">바로가기 →</a>`
                : '';
            card.innerHTML = `
                <div class="gift-emoji">${emoji}</div>
                <div class="gift-category">${gift.category}</div>
                <div class="gift-name">${gift.name}</div>
                <div class="gift-price">${gift.price.toLocaleString()}원</div>
                ${gift.target ? `<div class="gift-target">${gift.target}</div>` : ''}
                <div class="gift-score">매칭 +${gift.score}</div>
                ${linkBtn}
            `;
            resultsList.appendChild(card);
        });
    }

    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth" });
}