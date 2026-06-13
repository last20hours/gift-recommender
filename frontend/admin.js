const API_URL = "http://localhost:5001";

let currentPage = 1;
const PER_PAGE = 15;

window.addEventListener("DOMContentLoaded", () => loadGifts(1));
document.getElementById("searchInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") loadGifts(1);
});
async function loadGifts(page = 1) {
    currentPage = page;
    const search = document.getElementById("searchInput").value;
    const url = `${API_URL}/admin/gifts?page=${page}&per_page=${PER_PAGE}&search=${encodeURIComponent(search)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        renderTable(data.gifts);
        renderPagination(data);
        document.getElementById("totalInfo").textContent = 
            `총 ${data.total}개 / ${data.pages}페이지`;
    } catch (err) {
        showError(`데이터 로딩 실패: ${err.message}`);
    }
}
function renderTable(gifts) {
    const tbody = document.getElementById("giftTableBody");
    tbody.innerHTML = "";

    gifts.forEach(g => {
        const tr = document.createElement("tr");
        const genderLabel = { female: "여", male: "남", unisex: "공용" }[g.gender];
        tr.innerHTML = `
            <td>${g.id}</td>
            <td>${g.name}</td>
            <td>${g.category}</td>
            <td>${g.price.toLocaleString()}</td>
            <td>${genderLabel}</td>
            <td>${g.min_age}~${g.max_age}</td>
            <td class="actions">
                <button class="btn btn-secondary" onclick='editGift(${JSON.stringify(g)})'>수정</button>
                <button class="btn btn-danger" onclick="deleteGift(${g.id}, '${g.name}')">삭제</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
function openModal(gift = null) {
    document.getElementById("modal").classList.remove("hidden");
    document.getElementById("modalTitle").textContent = gift ? "선물 수정" : "새 선물 추가";
    
    if (gift) {
        // 수정 모드: 기존 값 채우기
        document.getElementById("editId").value = gift.id;
        document.getElementById("editName").value = gift.name;
        document.getElementById("editCategory").value = gift.category;
        document.getElementById("editPrice").value = gift.price;
        document.getElementById("editGender").value = gift.gender;
        document.getElementById("editAgeRange").value = `${gift.min_age}-${gift.max_age}`;
        document.getElementById("editTarget").value = gift.target || "";
        document.getElementById("editLink").value = gift.link || "";
    } else {
        // 추가 모드: 폼 초기화
        document.getElementById("giftEditForm").reset();
        document.getElementById("editId").value = "";
    }
}

function closeModal() {
    document.getElementById("modal").classList.add("hidden");
}
document.getElementById("giftEditForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("editId").value;
    const [min_age, max_age] = document.getElementById("editAgeRange").value.split("-").map(Number);
    
    const payload = {
        name: document.getElementById("editName").value,
        category: document.getElementById("editCategory").value,
        price: parseInt(document.getElementById("editPrice").value),
        gender: document.getElementById("editGender").value,
        min_age, max_age,
        target: document.getElementById("editTarget").value || null,
        link: document.getElementById("editLink").value || null,
    };

    // ID 있으면 PUT(수정), 없으면 POST(생성)
    const url = id ? `${API_URL}/admin/gifts/${id}` : `${API_URL}/admin/gifts`;
    const method = id ? "PUT" : "POST";

    try {
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("저장 실패");
        closeModal();
        loadGifts(currentPage);
    } catch (err) {
        alert(`❌ ${err.message}`);
    }
});
async function deleteGift(id, name) {
    if (!confirm(`정말 "${name}"을(를) 삭제하시겠습니까?`)) return;
    try {
        const res = await fetch(`${API_URL}/admin/gifts/${id}`, { method: "DELETE" });
        if (!res.ok) throw new Error("삭제 실패");
        loadGifts(currentPage);
    } catch (err) {
        alert(`❌ ${err.message}`);
    }
}