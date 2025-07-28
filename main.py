
# !/usr/bin/env python3
"""
LinkedIn Job Scraper
A Python script to scrape job postings from LinkedIn for a specific title and location.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import quote_plus


def get_job_ids(title, location, start=0):
    """
    Get job IDs from LinkedIn job search results.

    Args:
        title (str): Job title to search for
        location (str): Job location
        start (int): Starting point for pagination

    Returns:
        list: List of job IDs
    """
    # URL encode the parameters to handle special characters
    encoded_title = quote_plus(title)
    encoded_location = quote_plus(location)

    # Construct the URL for LinkedIn job search
    list_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_title}&location={encoded_location}&start={start}"

    print(f"Fetching job listings from: {list_url}")

    try:
        # Send a GET request to the URL with headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(list_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the HTML response
        list_soup = BeautifulSoup(response.text, "html.parser")
        page_jobs = list_soup.find_all("li")

        # Extract job IDs
        id_list = []
        for job in page_jobs:
            try:
                base_card_div = job.find("div", {"class": "base-card"})
                if base_card_div and base_card_div.get("data-entity-urn"):
                    job_id = base_card_div.get("data-entity-urn").split(":")[3]
                    print(f"Found job ID: {job_id}")
                    id_list.append(job_id)
            except (AttributeError, IndexError) as e:
                print(f"Error extracting job ID: {e}")
                continue

        return id_list

    except requests.RequestException as e:
        print(f"Error fetching job listings: {e}")
        return []


def scrape_job_details(job_id):
    """
    Scrape detailed information for a specific job ID.

    Args:
        job_id (str): LinkedIn job ID

    Returns:
        dict: Dictionary containing job details
    """
    job_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        job_response = requests.get(job_url, headers=headers)
        print(f"Job {job_id} - Status code: {job_response.status_code}")
        job_response.raise_for_status()

        job_soup = BeautifulSoup(job_response.text, "html.parser")

        # Create a dictionary to store job details
        job_post = {"job_id": job_id}

        # Try to extract and store the job title
        try:
            job_title_elem = job_soup.find("h2", {
                "class": "top-card-layout__title font-sans text-lg papabear:text-xl font-bold leading-open text-color-text mb-0 topcard__title"
            })
            job_post["job_title"] = job_title_elem.text.strip() if job_title_elem else None
        except AttributeError:
            job_post["job_title"] = None

        # Try to extract and store the company name
        try:
            company_elem = job_soup.find("a", {
                "class": "topcard__org-name-link topcard__flavor--black-link"
            })
            job_post["company_name"] = company_elem.text.strip() if company_elem else None
        except AttributeError:
            job_post["company_name"] = None

        # Try to extract and store the time posted
        try:
            time_elem = job_soup.find("span", {
                "class": "posted-time-ago__text topcard__flavor--metadata"
            })
            job_post["time_posted"] = time_elem.text.strip() if time_elem else None
        except AttributeError:
            job_post["time_posted"] = None

        # Try to extract and store the number of applicants
        try:
            applicants_elem = job_soup.find("span", {
                "class": "num-applicants__caption topcard__flavor--metadata topcard__flavor--bullet"
            })
            job_post["num_applicants"] = applicants_elem.text.strip() if applicants_elem else None
        except AttributeError:
            job_post["num_applicants"] = None

        # Try to extract job location
        try:
            location_elem = job_soup.find("span", {
                "class": "topcard__flavor topcard__flavor--bullet"
            })
            job_post["location"] = location_elem.text.strip() if location_elem else None
        except AttributeError:
            job_post["location"] = None

        return job_post

    except requests.RequestException as e:
        print(f"Error fetching job {job_id}: {e}")
        return {"job_id": job_id, "job_title": None, "company_name": None,
                "time_posted": None, "num_applicants": None, "location": None}


def main():
    """
    Main function to orchestrate the job scraping process.
    """
    # Configuration
    title = "Python Developer"  # Job title
    location = "Toronto"  # Job location
    start = 0  # Starting point for pagination
    output_filename = f"{location.replace(' ', '_')}_{title.replace(' ', '_')}_jobs.csv"

    print(f"Starting LinkedIn job scraper for '{title}' in '{location}'")
    print("=" * 60)

    # Get job IDs
    print("Step 1: Fetching job IDs...")
    id_list = get_job_ids(title, location, start)

    if not id_list:
        print("No job IDs found. Exiting.")
        return

    print(f"Found {len(id_list)} job IDs")

    # Scrape job details
    print("\nStep 2: Scraping job details...")
    job_list = []

    for i, job_id in enumerate(id_list, 1):
        print(f"Processing job {i}/{len(id_list)}: {job_id}")
        job_details = scrape_job_details(job_id)
        job_list.append(job_details)

        # Add a random delay to be respectful to the server
        delay = random.uniform(1, 3)
        time.sleep(delay)

    # Convert to DataFrame and save
    print("\nStep 3: Saving data...")
    if job_list:
        jobs_df = pd.DataFrame(job_list)

        # Display basic info about the scraped data
        print(f"\nScraped {len(jobs_df)} jobs")
        print("\nData preview:")
        print(jobs_df.head())

        # Save to CSV
        jobs_df.to_csv(output_filename, index=False)
        print(f"\nData saved to: {output_filename}")

        # Display summary statistics
        print("\nSummary:")
        print(f"- Total jobs scraped: {len(jobs_df)}")
        print(f"- Jobs with titles: {jobs_df['job_title'].notna().sum()}")
        print(f"- Jobs with company names: {jobs_df['company_name'].notna().sum()}")
        print(f"- Jobs with applicant counts: {jobs_df['num_applicants'].notna().sum()}")

    else:
        print("No job data was successfully scraped.")


if __name__ == "__main__":
    main()