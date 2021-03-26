import sys
import click
import argparse

from scrapper import LinkedInScrapper


class CustomFormatter(argparse.RawDescriptionHelpFormatter,
                      argparse.ArgumentDefaultsHelpFormatter):
    pass


def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(formatter_class=CustomFormatter, description="LinkedIn Open-to-work bot")

    parser.add_argument("-e", "--email", type=str, help="Your linkedIn email address", required=True)
    parser.add_argument("-p", "--password", type=str, help="Your linkedIn password", required=True)
    parser.add_argument("-l", "--headless", type=bool, help="Open firebox browser.", default=False)

    return parser.parse_args(args)


def main(email, password, headless):
    scrapper = LinkedInScrapper(email=email,
                                password=password,
                                headless=headless)
    scrapper.feed_page()

    while True:
        scrapper.search_for_people_open_to_work()
        if scrapper.current_page == scrapper.number_of_pages:
            break

    click.echo(click.style("GETTING USER PROFILE", bold=True, underline=True, fg="blue"))

    for profile_url in scrapper.user_profile_urls:
        scrapper.profile_contact(profile_url)

    scrapper.write_user_email_address_to_file()


if __name__ == "__main__":
    args = parse_args()
    main(args.email, args.password, args.headless)



